import logging
from datetime import datetime
from typing import Self, Optional

from django.db import models

from actions_data.models import (
    Repository,
    PullRequest,
    OwnerEntity,
    Workflow,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class WorkflowRunManager(models.Manager):

    def get_or_create_from_payload(self, payload: dict) -> "WorkflowRun":
        run = payload["workflow_run"]
        pull_requests_data = run.get("pull_requests", [])
        pull_requests = PullRequest.get_or_create_from_dict_list(pull_requests_data)

        actor_data = run.get("actor", {})
        actor = OwnerEntity.get_or_create_from_dict(actor_data)

        triggering_actor_data = run.get("triggering_actor", {})
        triggering_actor = OwnerEntity.get_or_create_from_dict(triggering_actor_data)

        repository_data = run.get("repository", {})
        repository = Repository.objects.get_or_create_from_dict(repository_data)

        head_repository_data = run.get("head_repository")
        head_repository = None
        if head_repository_data:
            head_repository = Repository.objects.get_or_create_from_dict(
                head_repository_data
            )

        workflow_data = payload.get("workflow")
        workflow = None
        if workflow_data:
            workflow = Workflow.get_or_create_from_webhook_payload(
                workflow_data, repository.id
            )

        result = self.update_or_create(
            run_id=run["id"],
            run_attempt=run["run_attempt"],
            defaults={
                "name": run["name"],
                "node_id": run["node_id"],
                "head_branch": run["head_branch"],
                "head_sha": run["head_sha"],
                "path": run["path"],
                "display_title": run["display_title"],
                "run_number": run["run_number"],
                "event": run["event"],
                "status": run["status"],
                "conclusion": run["conclusion"],
                "workflow_id": run["workflow_id"],
                "check_suite_id": run["check_suite_id"],
                "check_suite_node_id": run["check_suite_node_id"],
                "url": run["url"],
                "html_url": run["html_url"],
                "created_at": run["created_at"],
                "updated_at": run["updated_at"],
                "actor": actor,
                # referenced_workflows=[]
                "run_started_at": run["run_started_at"],
                "triggering_actor": triggering_actor,
                "jobs_url": run["jobs_url"],
                "logs_url": run["logs_url"],
                "check_suite_url": run["check_suite_url"],
                "artifacts_url": run["artifacts_url"],
                "cancel_url": run["cancel_url"],
                "rerun_url": run["rerun_url"],
                "previous_attempt_url": run["previous_attempt_url"],
                "workflow_url": run["workflow_url"],
                "head_commit": run["head_commit"]["id"],
                "repository": repository,
                "head_repository": head_repository,
            },
        )[0]
        result.pull_requests.add(*pull_requests)
        result.save()
        return result

    def get_or_create_from_webhook_event(
        self, event: WebhookEvent
    ) -> Optional["WorkflowRun"]:
        if not event.is_processable_webhook_event:
            logger.warning(f"Received a non-processable WebhookEvent: {event}")
        result = self.get_or_create_from_payload(event.payload)
        result.webhook_events.add(event)
        result.installation = event.associate_installation()
        result.repository.last_webhook_received = datetime.now()
        result.save()
        result.save_redundant_data_to_jobs()
        return result

    def create_empty_workflow_run(
        self, run_id: int, run_attempt: int, repo_id: int
    ) -> Self:
        return self.create(
            run_id=run_id, run_attempt=run_attempt, repository_id=repo_id
        )

    def get_or_create_from_run_id_attempt_and_repo_data(
        self, run_id: int, run_attempt: int, repo_data: dict
    ) -> Self:
        try:
            workflow_run = self.get(run_id=run_id, run_attempt=run_attempt)
        except self.model.DoesNotExist:
            repository = Repository.objects.get_or_create_from_dict(repo_data)
            workflow_run = self.create_empty_workflow_run(
                run_id=run_id, run_attempt=run_attempt, repo_id=repository.id
            )
        workflow_run.repository.last_webhook_received = datetime.now()
        return workflow_run

    def filter_for_user(self, user: "User"):
        user_distinct_repo_ids = user.userprofile.repositories.values_list(
            "id", flat=True
        ).distinct()
        return self.filter(repository_id__in=user_distinct_repo_ids)


class WorkflowRun(models.Model):
    run_id = models.PositiveBigIntegerField()
    name = models.CharField(max_length=1000, null=True)
    node_id = models.CharField(max_length=500, null=True)
    head_branch = models.CharField(max_length=500, null=True)
    head_sha = models.CharField(max_length=500, null=True)
    path = models.CharField(max_length=500, null=True)
    display_title = models.CharField(max_length=1000, null=True)
    run_number = models.IntegerField(null=True)
    event = models.CharField(max_length=50, null=True)
    status = models.CharField(max_length=50, null=True)
    conclusion = models.CharField(max_length=50, null=True)
    workflow = models.ForeignKey(
        "Workflow", on_delete=models.CASCADE, related_name="workflow_runs", null=True
    )
    check_suite_id = models.PositiveBigIntegerField(null=True)
    check_suite_node_id = models.CharField(max_length=500, null=True)
    url = models.URLField(null=True)
    html_url = models.URLField(null=True)

    pull_requests = models.ManyToManyField("PullRequest")

    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    actor = models.ForeignKey(
        "OwnerEntity",
        on_delete=models.CASCADE,
        related_name="workflows_as_actor",
        null=True,
    )
    run_attempt = models.IntegerField(null=True)
    referenced_workflows = models.ManyToManyField(
        "Workflow", related_name="workflows_were_referenced"
    )
    run_started_at = models.DateTimeField(null=True)
    triggering_actor = models.ForeignKey(
        "OwnerEntity",
        on_delete=models.CASCADE,
        related_name="workflows_as_triggering_actor",
        null=True,
    )
    jobs_url = models.URLField(null=True)
    logs_url = models.URLField(null=True)
    check_suite_url = models.URLField(null=True)
    artifacts_url = models.URLField(null=True)
    cancel_url = models.URLField(null=True)
    rerun_url = models.URLField(null=True)
    previous_attempt_url = models.URLField(null=True)
    workflow_url = models.URLField(null=True)
    head_commit = models.CharField(max_length=500, null=True)  # this needs fixing
    repository = models.ForeignKey(
        "Repository", on_delete=models.CASCADE, related_name="workflows_as_repository"
    )
    head_repository = models.ForeignKey(
        "Repository",
        on_delete=models.CASCADE,
        related_name="workflows_as_head_repository",
        null=True,
    )
    webhook_events = models.ManyToManyField("WebhookEvent")
    job_data_collected = models.BooleanField(default=False)
    installation = models.ForeignKey(
        "Installation",
        on_delete=models.CASCADE,
        null=True,
        related_name="workflow_runs",
    )

    objects = WorkflowRunManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run_id", "run_attempt"], name="unique_run_attempt"
            ),
        ]
        indexes = [
            models.Index(fields=["id", "repository_id"]),
        ]

    def __str__(self):
        return f"{self.workflow.name} - {self.repository.name} - {self.status}"

    def save_redundant_data_to_jobs(self):
        for job in self.jobs.all():
            job.save_job_stats_entry()
