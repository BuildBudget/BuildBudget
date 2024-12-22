import logging
from datetime import datetime
from typing import Optional

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.dateparse import parse_datetime

from actions_data.models import WebhookEvent, JobStats, WorkflowRun

logger = logging.getLogger(__name__)


def minimum_started_at(steps: list) -> Optional[datetime]:
    current = None
    for step in steps:
        if step.get("started_at"):
            timestamp = parse_datetime(step["started_at"])
            if not current or timestamp < current:
                current = timestamp
    return current


def maximum_completed_at(steps: list) -> Optional[datetime]:
    current = None
    for step in steps:
        if step.get("completed_at"):
            timestamp = parse_datetime(step["completed_at"])
            if not current or timestamp > current:
                current = timestamp
    return current


def get_started_at(payload: dict) -> datetime:
    steps = payload.get("steps", [])
    from_steps = minimum_started_at(steps)
    from_payload = parse_datetime(payload["started_at"])
    if from_steps:
        return min(from_steps, from_payload)
    return from_payload


def get_completed_at(payload: dict) -> datetime:
    steps = payload.get("steps", [])
    from_steps = maximum_completed_at(steps)
    from_payload = parse_datetime(payload["completed_at"])
    if from_steps:
        return max(from_steps, from_payload)
    return from_payload


class JobManager(models.Manager):

    def get_or_create_from_payload(self, payload: dict) -> "Job":
        job = payload["workflow_job"]
        return self.update_or_create(
            id=job["id"],
            defaults={
                "node_id": job["node_id"],
                "url": job["url"],
                "html_url": job["html_url"],
                "name": job["name"],
                "status": job["status"],
                "conclusion": job["conclusion"],
                "created_at": job["created_at"],
                "started_at": get_started_at(job),
                "completed_at": get_completed_at(job),
                "steps": job["steps"],
                "check_run_url": job["check_run_url"],
                "labels": job["labels"],
                "runner_id": job["runner_id"],
                "runner_name": job["runner_name"],
                "runner_group_id": job["runner_group_id"],
                "runner_group_name": job["runner_group_name"],
            },
        )[0]

    def get_or_create_from_webhook_event(
        self, event: "WebhookEvent"
    ) -> Optional["Job"]:
        if not event.is_processable_webhook_event:
            logger.warning(f"Received a non-processable event: {event}")
            raise ValueError("Received a non-processable event")
        job = self.get_or_create_from_payload(event.payload)
        job.webhook_events.add(event)

        run_id = event.payload["workflow_job"]["run_id"]
        run_attempt = event.payload["workflow_job"]["run_attempt"]
        repo_data = event.payload["repository"]
        job.workflow_run = (
            WorkflowRun.objects.get_or_create_from_run_id_attempt_and_repo_data(
                run_id, run_attempt, repo_data
            )
        )
        job.installation = event.installation
        job.save()
        job.save_job_stats_entry()
        return job

    def count_for_run_attempt(
        self, owner: str, repo: str, run_id: int, run_attempt: int
    ) -> int:
        return self.filter(
            workflow_run__run_id=run_id,
            workflow_run__run_attempt=run_attempt,
            workflow_run__repository__owner__login=owner,
            workflow_run__repository__name=repo,
        ).count()


class Job(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    workflow_run = models.ForeignKey(
        "WorkflowRun", on_delete=models.CASCADE, null=True, related_name="jobs"
    )
    node_id = models.CharField(max_length=500, null=True)
    url = models.URLField(null=True)
    html_url = models.URLField(null=True)
    name = models.CharField(max_length=1000)
    status = models.CharField(max_length=50)
    conclusion = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(auto_now=True)
    steps = models.JSONField(null=True)
    check_run_url = models.URLField(null=True)
    labels = models.JSONField(null=True)
    runner_id = models.IntegerField(null=True)
    runner_name = models.CharField(max_length=500, null=True)
    runner_group_id = models.IntegerField(null=True)
    runner_group_name = models.CharField(max_length=500, null=True)
    webhook_events = models.ManyToManyField("WebhookEvent")
    installation = models.ForeignKey(
        "Installation", on_delete=models.CASCADE, null=True, related_name="jobs"
    )

    objects = JobManager()

    class Meta:
        indexes = [
            models.Index(fields=["workflow_run_id"]),
            models.Index(fields=["started_at"]),
            GinIndex(fields=["labels"], name="idx_job_labels_gin"),
        ]

    def __str__(self):
        return f"{self.workflow_run_id} - {self.id} - {self.name} - {self.status}"

    def save_job_stats_entry(self) -> Optional[JobStats]:
        self.refresh_from_db()
        if (
            not self.workflow_run
            or not self.workflow_run.workflow
            or not self.started_at
            or not self.completed_at
        ):
            return

        result, created = JobStats.objects.update_or_create(
            job_id=self.id,
            defaults={
                "workflow_run": self.workflow_run,
                "workflow": self.workflow_run.workflow,
                "repository": self.workflow_run.repository,
                "owner_entity": self.workflow_run.repository.owner,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "installation": self.installation,
            },
        )
        return result
