from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from github.Installation import Installation as ClientInstallation


@dataclass
class ExtendedInstallation:

    installation: ClientInstallation

    @property
    def app_slug(self) -> str:
        return self.installation.raw_data.get("app_slug")

    @property
    def client_id(self) -> str:
        return self.installation.raw_data.get("client_id")

    @property
    def access_tokens_url(self) -> str:
        return self.installation.raw_data.get("access_tokens_url")

    @property
    def html_url(self) -> str:
        return self.installation.raw_data.get("html_url")

    @property
    def repositories_url(self) -> str:
        return self.installation.raw_data.get("repositories_url")

    @property
    def repository_selection(self) -> str:
        return self.installation.raw_data.get("repository_selection")

    @property
    def has_multiple_single_files(self) -> bool:
        return self.installation.raw_data.get("has_multiple_single_files")

    @property
    def single_file_name(self) -> str:
        return self.installation.raw_data.get("single_file_name")

    @property
    def single_file_paths(self) -> list:
        return self.installation.raw_data.get("single_file_paths")

    @property
    def events(self) -> list:
        return self.installation.raw_data.get("events")

    @property
    def permissions(self) -> dict:
        return self.installation.raw_data.get("permissions")

    @property
    def created_at(self) -> str:
        return self.installation.raw_data.get("created_at")

    @property
    def updated_at(self) -> str:
        return self.installation.raw_data.get("updated_at")

    @property
    def suspended_at(self) -> str:
        return self.installation.raw_data.get("suspended_at")

    @property
    def suspended_by(self) -> dict:
        return self.installation.raw_data.get("suspended_by")


class InstallationManager(models.Manager):
    def demo_installation(self):
        return self.get(
            is_artificial=True, installation_id=settings.DEMO_INSTALLATION_ID
        )

    def get_or_create_artificial_installation(
        self, enterprise_host: str, webhook_id: int
    ) -> "Installation":
        result, _ = self.get_or_create(
            is_artificial=True,
            enterprise_host=enterprise_host,
            webhook_id=webhook_id,
        )
        return result

    def update_or_create_from_client_instance(
        self, installation: ClientInstallation
    ) -> "Installation":
        ext_installation = ExtendedInstallation(installation)
        account = None
        result, _ = self.update_or_create(
            installation_id=installation.id,
            is_artificial=False,
            defaults={
                "app_id": installation.app_id,
                "app_slug": ext_installation.app_slug,
                "client_id": ext_installation.client_id,
                "access_tokens_url": ext_installation.access_tokens_url,
                "html_url": ext_installation.html_url,
                "repositories_url": ext_installation.repositories_url,
                "account": account,
                "repository_selection": ext_installation.repository_selection,
                "target_id": installation.target_id,
                "target_type": installation.target_type,
                "has_multiple_single_files": ext_installation.has_multiple_single_files,
                "single_file_name": ext_installation.single_file_name,
                "single_file_paths": ext_installation.single_file_paths,
                "events": ext_installation.events,
                "permissions": ext_installation.permissions,
                "created_at": ext_installation.created_at,
                "updated_at": ext_installation.updated_at,
                "suspended_at": ext_installation.suspended_at,
                "suspended_by": ext_installation.suspended_by,
            },
        )
        return result


class Installation(models.Model):
    # Core installation fields
    installation_id = models.BigIntegerField(
        null=True, help_text="GitHub installation ID"
    )
    app_id = models.BigIntegerField(help_text="GitHub App ID", null=True)
    app_slug = models.CharField(max_length=255, null=True)
    client_id = models.CharField(max_length=255, null=True)

    # URLs
    access_tokens_url = models.URLField(max_length=500, null=True)
    html_url = models.URLField(max_length=500, null=True)
    repositories_url = models.URLField(max_length=500, null=True)

    # Relationships
    account = models.ForeignKey(
        "OwnerEntity",
        on_delete=models.CASCADE,
        related_name="github_installations",
        null=True,
    )

    # Installation configuration
    repository_selection = models.CharField(max_length=50, null=True)
    target_id = models.BigIntegerField(null=True)
    target_type = models.CharField(max_length=50, null=True)

    # File-related fields
    has_multiple_single_files = models.BooleanField(default=False)
    single_file_name = models.CharField(max_length=255, null=True, blank=True)
    single_file_paths = models.JSONField(default=list)

    # Events and permissions
    events = models.JSONField(default=list)
    permissions = models.JSONField(default=dict)

    # Timestamps
    created_at = models.DateTimeField(null=True, default=now)
    updated_at = models.DateTimeField(null=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspended_by = models.JSONField(null=True, blank=True)

    # Internal
    is_artificial = models.BooleanField(default=False)
    users = models.ManyToManyField(User, related_name="installations")
    webhook_id = models.BigIntegerField(null=True, blank=True)
    enterprise_host: models.CharField = models.CharField(
        max_length=255, null=True, default="github.com"
    )

    # Manager
    objects = InstallationManager()

    class Meta:
        indexes = [
            models.Index(fields=["app_id"]),
            models.Index(fields=["target_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["installation_id", "enterprise_host"],
                name="unique_installation_id",
            )
        ]

    def __str__(self):
        return f"Installation {self.id} for {self.account}"
