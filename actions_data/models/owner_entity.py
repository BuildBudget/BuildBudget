from typing import Self

from django.contrib.auth.models import User
from django.urls import reverse
from github.NamedUser import NamedUser as ClientNamedUser
from django.db import models


class OwnerEntityManager(models.Manager):
    def filter_for_user(self, user: User) -> Self:
        user_distinct_repo_ids = user.userprofile.repositories.values_list(
            "id", flat=True
        ).distinct()
        return self.filter(repositories__in=user_distinct_repo_ids).distinct()


class OwnerEntity(models.Model):

    class EntityTypes(models.TextChoices):
        USER = "User"
        ORGANIZATION = "Organization"

    id = models.IntegerField(primary_key=True)
    login = models.CharField(max_length=100)
    avatar_url = models.URLField(null=True)
    api_token = models.CharField(max_length=100, null=True, blank=True)
    entity_type = models.CharField(max_length=50, choices=EntityTypes.choices)
    auth_members = models.ManyToManyField(
        User, through="Membership", related_name="organizations"
    )
    webhook_enabled = models.BooleanField(default=False)
    fetch_from_api = models.BooleanField(default=False)
    objects = OwnerEntityManager()

    class Meta:
        indexes = [
            models.Index(
                fields=["login"], include=["id"], name="idx_ownerentity_login_id"
            ),
        ]

    def __str__(self):
        return self.login

    def get_full_name(self):
        return self.login

    def get_absolute_url(self):
        return reverse("organization_stats", kwargs={"pk": self.pk})

    def get_demo_url(self):
        return reverse("demo_organization_stats", kwargs={"pk": self.pk})

    @classmethod
    def get_or_create_from_dict(cls, data: dict) -> Self:
        return cls.objects.update_or_create(
            id=data["id"],
            defaults={
                "avatar_url": data["avatar_url"],
                "entity_type": data["type"],
                "login": data["login"],
            },
        )[0]

    @classmethod
    def get_or_create_from_client_response(cls, data: ClientNamedUser) -> Self:
        return cls.objects.update_or_create(
            id=data.id,
            login=data.login,
            avatar_url=data.avatar_url,
            entity_type=data.type,
        )[0]
