import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Type, Optional, Generic

from github import (
    Github,
    Auth,
    Repository,
    GithubObject,
)
from dotenv import load_dotenv
from github import GithubRetry
from github.Auth import AppUserAuth
from github.Installation import Installation
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.PaginatedList import PaginatedListBase, PaginatedList
from github.WorkflowRun import WorkflowRun
from github.WorkflowJob import WorkflowJob
from github.Workflow import Workflow
from django.conf import settings

load_dotenv()
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=GithubObject)


class GitHubClient(Generic[T]):
    def __init__(self, api_token: str):
        self.auth = Auth.Token(token=api_token)

    def __enter__(self):
        statuses = list(range(500, 600))
        retry = GithubRetry(status_forcelist=statuses)
        self.client = Github(retry=retry, auth=self.auth)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    @property
    def requester(self):
        return self.client._Github__requester

    def get_object_from_url(self, url: str, obj_class: Type[T]) -> T:
        headers, data = self.requester.requestJsonAndCheck("GET", url)
        return obj_class(self.requester, headers, data, completed=True)

    def get_paginated_list(
        self, url: str, obj_class: Type[T], list_item: str
    ) -> PaginatedList[T]:
        return PaginatedList(obj_class, self.requester, url, None, list_item=list_item)

    def get_repo(self, repo_path: str) -> Repository:
        return self.client.get_repo(repo_path)

    def get_organization(self, org_name: str) -> Organization:
        return self.client.get_organization(org_name)


@dataclass
class UserRepo:
    repo: Repository
    installation: Installation


@dataclass
class UserOrg:
    org: NamedUser
    user_repos: list[UserRepo]

    @property
    def installations(self) -> list[Installation]:
        return [repo.installation for repo in self.user_repos]


def extract_installations(user_orgs: list[UserOrg]) -> list[Installation]:
    return [
        installation
        for user_org in user_orgs
        for installation in user_org.installations
    ]


def get_run_attempt_from_url(url: str, api_token: str) -> WorkflowRun:
    with GitHubClient(api_token) as client:
        return client.get_object_from_url(url, WorkflowRun)


def get_workflow_from_url(url: str, api_token: str) -> Workflow:
    with GitHubClient(api_token) as client:
        return client.get_object_from_url(url, Workflow)


def get_jobs_from_url(url: str, api_token: str) -> PaginatedList[WorkflowJob]:
    with GitHubClient(api_token) as client:
        return client.get_paginated_list(url, WorkflowJob, "jobs")


def get_workflow_runs_for_repo(
    owner: str, repo: str, api_token: str, starting_time: datetime
) -> PaginatedListBase[WorkflowRun]:
    starting_date_query = f">={starting_time.isoformat()}"
    with GitHubClient(api_token) as client:
        return client.get_repo(f"{owner}/{repo}").get_workflow_runs(
            created=starting_date_query
        )


def get_user_accessible_app_repos(user_token: str) -> list[UserRepo]:
    app_auth = Auth.AppAuth(
        settings.GITHUB_APP_APP_ID, private_key=settings.GITHUB_APP_PRIVATE_KEY
    )
    app_user_auth = AppUserAuth(
        settings.GITHUB_APP_APP_ID,
        settings.GITHUB_APP_PRIVATE_KEY,
        user_token,
    )

    with Github(retry=None, auth=app_user_auth) as gh:
        user = gh.get_user()
        user_repos = set(repo.full_name for repo in user.get_repos())
        result = []

        for installation in user.get_installations():
            installation_auth = app_auth.get_installation_auth(installation.id)
            installation._requester = installation._requester.withAuth(
                installation_auth
            )
            for repo in installation.get_repos():
                if repo.full_name in user_repos:
                    result.append(UserRepo(repo=repo, installation=installation))
        return result


def list_organization_repositories(
    api_token: str, org_name: str
) -> tuple[Organization, PaginatedListBase[Repository]]:
    with GitHubClient(api_token) as client:
        org = client.get_organization(org_name)
        return org, org.get_repos(sort="pushed", direction="desc")


def repo_list_to_org_list(user_repos: list[UserRepo]) -> list[UserOrg]:
    org_dict = defaultdict(list)
    for user_repo in user_repos:
        org = user_repo.repo.owner
        org_dict[org.login].append(user_repo)

    def create_user_org(org_login: str, org_user_repos: list[UserRepo]) -> UserOrg:
        org = next(
            user_repo.repo.owner
            for user_repo in user_repos
            if user_repo.repo.owner.login == org_login
        )
        return UserOrg(
            org=org,
            user_repos=sorted(org_user_repos, key=lambda r: r.repo.name.lower()),
        )

    def org_sort_key(user_org: UserOrg) -> tuple[int, str]:
        is_personal = user_org.org.type.lower() == "user"
        return 0 if is_personal else 1, user_org.org.login.lower()

    result = [
        create_user_org(org_login, org_user_repos)
        for org_login, org_user_repos in org_dict.items()
    ]
    return sorted(result, key=org_sort_key)


def get_github_orgs_and_repos_with_app_installed(
    api_token: Optional[str],
) -> list[UserOrg]:
    if not api_token:
        return []
    user_repos = get_user_accessible_app_repos(api_token)
    return repo_list_to_org_list(user_repos)
