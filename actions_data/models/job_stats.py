import logging
import math
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models

from actions_data.models import JobStatsLabel

TOLERANCE_SECONDS = 2
logger = logging.getLogger(__name__)


class JobStatsManager(models.Manager):

    def filter_for_user(self, user: "User"):
        user_distinct_repo_ids = user.userprofile.repositories.values_list(
            "id", flat=True
        ).distinct()
        return self.filter(repository_id__in=user_distinct_repo_ids)


class JobStats(models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="stats")
    job_name = models.CharField(max_length=1000, null=True)
    workflow_run = models.ForeignKey(
        "WorkflowRun", on_delete=models.CASCADE, related_name="stats"
    )
    workflow = models.ForeignKey(
        "Workflow", on_delete=models.CASCADE, related_name="stats"
    )
    workflow_name = models.CharField(max_length=1000, null=True)
    repository = models.ForeignKey(
        "Repository", on_delete=models.CASCADE, related_name="stats"
    )
    repository_name = models.CharField(max_length=1000, null=True)
    owner_entity = models.ForeignKey(
        "OwnerEntity", on_delete=models.CASCADE, related_name="stats"
    )
    owner_entity_name = models.CharField(max_length=1000, null=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    execution_time = models.DurationField(default=timedelta(0))
    billable_time = models.DurationField(default=timedelta(0))
    event = models.CharField(max_length=50, null=True)
    installation = models.ForeignKey(
        "Installation",
        on_delete=models.CASCADE,
        related_name="stats",
        null=True,
        blank=True,
    )
    objects = JobStatsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["job_id"], name="unique_job_stats_for_job")
        ]
        indexes = [
            models.Index(fields=["started_at"]),
            models.Index(fields=["started_at", "installation_id"]),
            models.Index(
                fields=["owner_entity_id", "repository_id", "workflow_id", "job_id"]
            ),
            models.Index(fields=["installation_id", "started_at"]),
            models.Index(fields=["workflow_id"]),
            models.Index(fields=["repository_id"]),
            models.Index(fields=["owner_entity_id"]),
            models.Index(fields=["repository_id", "started_at"]),
            models.Index(fields=["event"]),
            models.Index(fields=["workflow_run_id"]),
            models.Index(fields=["repository_id", "started_at", "event"]),
            models.Index(fields=["billable_time"]),
            models.Index(
                fields=[
                    "owner_entity_id",
                    "repository_id",
                    "workflow_id",
                    "job_id",
                    "started_at",
                ]
            ),
            models.Index(fields=["workflow_id", "owner_entity_id"]),
            models.Index(fields=["repository_id", "owner_entity_id", "started_at"]),
            models.Index(fields=["execution_time"]),
        ]

    def calculate_execution_times(self):
        self.execution_time = self.completed_at - self.started_at
        self.billable_time = timedelta(
            minutes=max(1, math.ceil(self.execution_time.total_seconds() / 60))
        )

    def save_labels(self):
        labels = self.job.labels
        if self.job.labels:
            for label in labels:
                JobStatsLabel.objects.get_or_create(job_stats=self, label=label)

    def save_event(self):
        self.event = self.workflow_run.event

    def save_names(self):
        self.job_name = self.job.name
        self.workflow_name = self.workflow.name
        self.repository_name = self.repository.name
        self.owner_entity_name = self.owner_entity.login

    def clean(self):
        # make completed_at equal to started_at if it is less than started_at for less than 2 seconds
        if self.completed_at < self.started_at:
            if (
                self.started_at - self.completed_at
            ).total_seconds() < TOLERANCE_SECONDS:
                self.completed_at = self.started_at
            else:
                raise ValidationError(
                    "completed_at should be greater than or equal to started_at"
                )

    def save(self, *args, **kwargs):
        self.save_event()
        self.save_names()
        self.full_clean()
        self.calculate_execution_times()
        super().save(*args, **kwargs)
        self.save_labels()
