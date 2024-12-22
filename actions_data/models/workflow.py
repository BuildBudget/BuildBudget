from typing import Self

from django.db import models
from django.urls import reverse
from github.Workflow import Workflow as ClientWorkflow


class WorkflowManager(models.Manager):
    def filter_for_user(self, user: "User"):
        user_distinct_repo_ids = user.userprofile.repositories.values_list(
            "id", flat=True
        ).distinct()
        return self.filter(repository_id__in=user_distinct_repo_ids)


class Workflow(models.Model):
    repository = models.ForeignKey("Repository", on_delete=models.CASCADE)
    id = models.IntegerField(primary_key=True)
    node_id = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=200)
    path = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    url = models.URLField(null=True)
    html_url = models.URLField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = WorkflowManager()

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.repository} - {self.name} [{self.state}]"

    @classmethod
    def get_or_create_from_client_response(
        cls, data: ClientWorkflow, repo_id: int
    ) -> Self:
        return Workflow.objects.update_or_create(
            id=data.id,
            name=data.name,
            path=data.path,
            state=data.state,
            url=data.url,
            html_url=data.html_url,
            repository_id=repo_id,
        )[0]

    @classmethod
    def get_or_create_from_webhook_payload(cls, data: dict, repo_id: int) -> Self:
        return Workflow.objects.update_or_create(
            id=data["id"],
            defaults={
                "repository_id": repo_id,
                "id": data["id"],
                "node_id": data["node_id"],
                "name": data["name"],
                "path": data["path"],
                "state": data["state"],
                "url": data["url"],
                "html_url": data["html_url"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
            },
        )[0]

    def get_full_name(self):
        return f"{self.repository.slug} - {self.name}"

    @classmethod
    def update_or_create_workflows_from_json(
        cls, data: list[dict], repo_id: int
    ) -> list[Self]:
        workflows = []
        for workflow in data:
            workflows.append(cls.get_or_create_from_dict(workflow, repo_id))
        return workflows

    def get_absolute_url(self):
        return reverse("workflow_stats", kwargs={"pk": self.pk})

    def get_demo_url(self):
        return reverse("demo_workflow_stats", kwargs={"pk": self.pk})
