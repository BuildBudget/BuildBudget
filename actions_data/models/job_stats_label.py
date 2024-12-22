from django.db import models


class JobStatsLabelManager(models.Manager):
    def filter_for_user(self, user: "User"):
        user_distinct_repo_ids = user.userprofile.repositories.values_list(
            "id", flat=True
        ).distinct()
        return self.filter(job_stats__repository_id__in=user_distinct_repo_ids)


class JobStatsLabel(models.Model):
    job_stats = models.ForeignKey(
        "JobStats", on_delete=models.CASCADE, related_name="labels"
    )
    label = models.CharField(max_length=255)
    objects = JobStatsLabelManager()

    class Meta:
        unique_together = ("job_stats", "label")
        indexes = [
            models.Index(fields=["job_stats_id"]),
            models.Index(fields=["job_stats_id", "label"]),
            models.Index(fields=["label"]),
        ]
