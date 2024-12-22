import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import timedelta
from itertools import cycle
import time
from typing import Iterator, TypeVar, Callable, Any
from functools import wraps

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from social_django.models import UserSocialAuth
from github import (
    RateLimitExceededException,
    WorkflowRun as ClientWorkflowRun,
    WorkflowJob as ClientJob,
    Repository as ClientRepository,
    Organization as ClientOrg,
    Workflow as ClientWorkflow,
)


from actions_data.github_client import (
    list_organization_repositories,
    get_jobs_from_url,
    get_workflow_runs_for_repo,
    get_run_attempt_from_url,
    get_workflow_from_url,
)
from actions_data.models import OwnerEntity, Repository, WebhookEvent, Installation

logger = logging.getLogger(__name__)

SENDER = {
    "login": "eduramirezh",
    "id": 1679647,
    "node_id": "MDQ6VXNlcjE2Nzk2NDc=",
    "avatar_url": "https://avatars.githubusercontent.com/u/1679647?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/eduramirezh",
    "html_url": "https://github.com/eduramirezh",
    "followers_url": "https://api.github.com/users/eduramirezh/followers",
    "following_url": "https://api.github.com/users/eduramirezh/following{/other_user}",
    "gists_url": "https://api.github.com/users/eduramirezh/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/eduramirezh/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/eduramirezh/subscriptions",
    "organizations_url": "https://api.github.com/users/eduramirezh/orgs",
    "repos_url": "https://api.github.com/users/eduramirezh/repos",
    "events_url": "https://api.github.com/users/eduramirezh/events{/privacy}",
    "received_events_url": "https://api.github.com/users/eduramirezh/received_events",
    "type": "User",
    "user_view_type": "public",
    "site_admin": False,
}

T = TypeVar("T")


def get_auth_tokens() -> list[str]:
    demo_users = UserSocialAuth.objects.filter(
        user__userprofile__use_as_global_token=True
    ).order_by("?")
    tokens = [user.extra_data["access_token"] for user in demo_users]
    return tokens


def get_attempts_urls(run: ClientWorkflowRun) -> list[str]:
    last_attempt = run.run_attempt
    base_url = run.url
    attempts = [f"{base_url}/attempts/{i}" for i in range(1, last_attempt + 1)]
    return attempts


@dataclass
class JobWebhookPayload:
    action: str
    workflow_job: dict
    repository: dict
    organization: dict
    sender: dict


@dataclass
class WorkflowRunWebhookPayload:
    action: str
    workflow_run: dict
    workflow: dict
    repository: dict
    organization: dict
    sender: dict


def demo_webhook_event_headers() -> dict:
    return {
        "delivery": str(uuid.uuid4()),
        "hook_id": settings.DEMO_WEBHOOK_ID,
        "hook_installation_target_type": "demo",
        "hook_installation_target_id": settings.DEMO_INSTALLATION_ID,
    }


def client_job_to_webhook_event_kwargs(
    org: ClientOrg, repo: ClientRepository, job: ClientJob
) -> dict:
    action = job.status
    workflow_job = job.raw_data
    repository = repo.raw_data
    organization = org.raw_data
    payload = JobWebhookPayload(
        action=action,
        workflow_job=workflow_job,
        repository=repository,
        organization=organization,
        sender=SENDER,
    )
    base = demo_webhook_event_headers()
    base["payload"] = asdict(payload)
    base["event"] = "workflow_job"
    return base


def client_run_attempt_to_webhook_event_kwargs(
    org: ClientOrg, repo: ClientRepository, wf: ClientWorkflow, wfr: ClientWorkflowRun
) -> dict:
    payload = WorkflowRunWebhookPayload(
        action=wfr.status,
        workflow_run=wfr.raw_data,
        workflow=wf.raw_data,
        repository=repo.raw_data,
        organization=org.raw_data,
        sender=SENDER,
    )
    base = demo_webhook_event_headers()
    base["payload"] = asdict(payload)
    base["event"] = "workflow_run"
    return base


def with_retries():
    """
    Decorator that implements retry logic for GitHub API calls.
    Will retry on RateLimitExceeded by rotating tokens and trying again.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self: "DemoDataPusher", *args, **kwargs) -> T:
            while True:
                try:
                    return func(self, *args, **kwargs)
                except RateLimitExceededException:
                    self.rotate_token()

        return wrapper

    return decorator


def link_demo_repos_to_demo_user():
    """
    This function links the demo repositories to the demo user to avoid hitting the rate limit of the GitHub API.
    Uses batch processing and iterator to reduce memory usage.
    """
    BATCH_SIZE = 1000  # Adjust based on your needs

    demo_user = User.objects.get(username=settings.DEMO_USERNAME)
    demo_user_profile = demo_user.userprofile
    demo_installation = Installation.objects.demo_installation()

    # Use values_list to only fetch IDs and iterator() to avoid loading all records at once
    repo_ids = (
        Repository.objects.filter(stats__installation=demo_installation)
        .values_list("id", flat=True)
        .distinct()
        .iterator()
    )

    processed_count = 0
    current_batch = []

    for repo_id in repo_ids:
        current_batch.append(repo_id)

        if len(current_batch) >= BATCH_SIZE:
            # Add repositories in batches
            demo_user_profile.repositories.add(*current_batch)
            processed_count += len(current_batch)
            current_batch = []

    # Add any remaining repositories
    if current_batch:
        demo_user_profile.repositories.add(*current_batch)
        processed_count += len(current_batch)

    logger.info(f"Successfully linked {processed_count} demo repos to the demo user")


class DemoDataPusher:
    """
    This class is responsible for fetching workflow data for the orgs marked as "fetch_from_api" from GitHub's API,
    and then push that data to the webhook events table to be processed by the webhook processor.
    The class uses a pool of demo users to avoid hitting the rate limit of the GitHub API.
    """

    def __init__(self, webhook_processing_function: callable):
        self.tokens = get_auth_tokens()
        self.tokens_pool: Iterator[str] = cycle(self.tokens)
        self.num_tokens = len(self.tokens)
        if self.num_tokens == 0:
            raise ValueError("No demo users found. Please create a demo user.")
        self.token = next(self.tokens_pool)
        self.orgs = OwnerEntity.objects.filter(fetch_from_api=True)
        if not self.orgs:
            raise ValueError("No orgs marked as 'fetch_from_api' found.")
        self.backoff_time = 60  # Initial backoff time in seconds
        self.process_webhook_event = webhook_processing_function

    def rotate_token(self):
        """Rotate to the next token, implementing exponential backoff if all tokens are exhausted"""
        self.token = next(self.tokens_pool)
        self.num_tokens -= 1
        logger.info(f"Rotating token. Number of tokens left: {self.num_tokens}")
        if self.num_tokens == 0:
            logger.warning(
                f"All tokens exhausted. Backing off for {self.backoff_time} seconds."
            )
            time.sleep(self.backoff_time)
            self.backoff_time *= 2  # Exponential backoff
            self.num_tokens = len(self.tokens)  # Reset token count

    @with_retries()
    def get_selected_repos_for_org(
        self, org_or_user: OwnerEntity
    ) -> tuple[ClientOrg, list[ClientRepository]]:
        org, repos = list_organization_repositories(self.token, org_or_user.login)
        selectable_repos = list(repos[:50])
        selected_repos = [
            repo
            for repo in selectable_repos
            if repo.pushed_at > timezone.now() - timedelta(days=30)
        ]
        logger.info(
            f"Porcessing {len(selected_repos)} repos for org '{org.login}'. The repos are: {selected_repos}"
        )
        for repo in selected_repos:
            repo._completeIfNeeded()
        return org, selected_repos

    @with_retries()
    def get_original_runs(
        self, repo: Repository, starting_time: timezone.datetime
    ) -> list[ClientWorkflowRun]:
        logger.debug(f"Getting runs for repo: {repo}")
        runs = list(
            get_workflow_runs_for_repo(
                repo.owner.login,
                repo.name,
                self.token,
                starting_time,
            )
        )
        for run in runs:
            run._completeIfNeeded()
        return runs

    @with_retries()
    def get_all_attempts_for_run_instance(
        self, run: ClientWorkflowRun
    ) -> list[ClientWorkflowRun]:
        """Fetch all attempts for a workflow run"""
        attempt_urls = get_attempts_urls(run)
        result = []
        for url in attempt_urls:
            attempt_instance = get_run_attempt_from_url(url, self.token)
            attempt_instance._completeIfNeeded()
            result.append(attempt_instance)
        return result

    @with_retries()
    def get_jobs_data_for_run_attempt(
        self, run_attempt: ClientWorkflowRun
    ) -> list[ClientJob]:
        logger.debug(f"Getting jobs for run attempt: {run_attempt}")
        jobs = list(get_jobs_from_url(run_attempt.jobs_url, self.token))
        for job in jobs:
            job._completeIfNeeded()
        return jobs

    @with_retries()
    def fetch_workflow(self, run: ClientWorkflowRun) -> ClientWorkflow:
        logger.debug(f"Fetching workflow for run: {run}")
        wf = get_workflow_from_url(run.workflow_url, self.token)
        wf._completeIfNeeded()
        return wf

    def save_job_webhook_event(
        self, org: ClientOrg, repo: ClientRepository, job: ClientJob
    ):
        logger.debug(f"Saving job webhook event: {job}")
        kwargs = client_job_to_webhook_event_kwargs(org, repo, job)
        created = WebhookEvent.objects.create(**kwargs)
        try:
            self.process_webhook_event(created.id)
        except Exception as e:
            logger.error(
                f"An error occurred processing job {job} for repo {repo}: {e}",
                exc_info=True,
            )

    def save_run_webhook_event(
        self,
        org: ClientOrg,
        repo: ClientRepository,
        wf: ClientWorkflow,
        wfr: ClientWorkflowRun,
    ):
        logger.debug(f"Saving run webhook event: {wfr}")
        kwargs = client_run_attempt_to_webhook_event_kwargs(org, repo, wf, wfr)
        created = WebhookEvent.objects.create(**kwargs)
        try:
            self.process_webhook_event(created.id)
        except Exception as e:
            logger.error(
                f"An error occurred processing run {wfr} for repo {repo}: {e}",
                exc_info=True,
            )

    def process_run_attempt(
        self,
        org: ClientOrg,
        repo: ClientRepository,
        wf: ClientWorkflow,
        run_attempt: ClientWorkflowRun,
    ):
        logger.debug(f"Processing run attempt: {run_attempt}")
        self.save_run_webhook_event(org, repo, wf, run_attempt)
        jobs = self.get_jobs_data_for_run_attempt(run_attempt)
        for job in jobs:
            self.save_job_webhook_event(org, repo, job)

    def process_repo(
        self, org: ClientOrg, repo: ClientRepository, starting_time: timezone.datetime
    ):
        runs = self.get_original_runs(repo, starting_time)
        processed_run_attempts = 0
        for run in runs:
            try:
                wf = self.fetch_workflow(run)
                run_attempts = self.get_all_attempts_for_run_instance(run)
                for run_attempt in run_attempts:
                    self.process_run_attempt(org, repo, wf, run_attempt)
                    processed_run_attempts += 1
            except Exception as e:
                logger.error(
                    f"An error occurred processing run {run} for repo {repo}: {e}",
                    exc_info=True,
                )
        logger.info(
            f"Processing for repo {repo} completed. Processed run attempts: {processed_run_attempts}"
        )

    def push_demo_data_to_webhook_events(self, started_time_ago: timedelta):
        starting_time = timezone.now() - started_time_ago
        for org in self.orgs:
            logger.info(f"Processing org: {org}")
            client_org, repositories = self.get_selected_repos_for_org(org)
            for repo in repositories:
                try:
                    self.process_repo(client_org, repo, starting_time)
                except Exception as e:
                    logger.error(
                        f"An error occurred processing repo {repo}: {e}",
                        exc_info=True,
                    )
        logger.info("Demo data push completed.")

    def run(self, started_time_ago: timedelta):
        try:
            link_demo_repos_to_demo_user()
            self.push_demo_data_to_webhook_events(started_time_ago)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
