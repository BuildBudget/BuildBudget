from django.db import models
from django.urls import reverse
from github.Repository import Repository as ClientRepository

from actions_data.models import OwnerEntity


class RepositoryManager(models.Manager):

    def get_or_create_from_client_response(
        self, repo: ClientRepository
    ) -> "Repository":
        owner_data = repo.owner
        owner = OwnerEntity.get_or_create_from_client_response(owner_data)
        return self.update_or_create(
            id=repo.id,
            defaults={
                "name": repo.name,
                "owner_id": owner.id,
            },
        )[0]

    def get_or_create_from_dict(self, data: dict) -> "Repository":
        owner_data = data.get("owner", {})
        owner = OwnerEntity.get_or_create_from_dict(owner_data)
        return self.update_or_create(
            id=data["id"],
            defaults={
                "name": data["name"],
                "owner_id": owner.id,
            },
        )[0]

    def filter_for_user(self, user: "User"):
        user_distinct_repo_ids = user.userprofile.repositories.values_list(
            "id", flat=True
        ).distinct()
        return self.filter(id__in=user_distinct_repo_ids)


class Repository(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    webhook_enabled = models.BooleanField(default=False)
    last_webhook_received = models.DateTimeField(null=True)
    owner = models.ForeignKey(
        "OwnerEntity", on_delete=models.CASCADE, related_name="repositories"
    )
    objects = RepositoryManager()

    class Meta:
        indexes = [
            models.Index(fields=["id", "owner_id"]),
            models.Index(fields=["name"]),
            models.Index(fields=["owner_id", "name"]),
        ]

    def __str__(self):
        return f"{self.owner.login}/{self.name}"

    @property
    def slug(self):
        return f"{self.owner.login}/{self.name}"

    def get_full_name(self):
        return self.slug

    def get_absolute_url(self):
        return reverse("repository_stats", kwargs={"pk": self.pk})

    def get_demo_url(self):
        return reverse("demo_repository_stats", kwargs={"pk": self.pk})

    def html_url(self):
        return f"https://github.com/{self.owner.login}/{self.name}"
