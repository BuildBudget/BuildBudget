from django.contrib.auth.models import User
from django.db import models

from actions_data.models import Installation

DEFAULT_HOST = "github.com"
DELIVERY_HEADER = "X-Github-Delivery"
EVENT_HEADER = "X-Github-Event"
HOOK_ID_HEADER = "X-Github-Hook-ID"
HOOK_INSTALLATION_TARGET_ID_HEADER = "X-Github-Hook-Installation-Target-ID"
HOOK_INSTALLATION_TARGET_TYPE_HEADER = "X-Github-Hook-Installation-Target-Type"
ENTERPRISE_VERSION_HEADER = "X-Github-Enterprise-Version"
ENTERPRISE_HOST_HEADER = "X-Github-Enterprise-Host"


class WebhookEventManager(models.Manager):
    def create_from_headers_and_payload(self, **kwargs):
        headers = kwargs.get("headers")
        payload = kwargs.get("payload")
        user_id = kwargs.get("user_id")
        return self.create(
            payload=payload,
            delivery=headers.get(DELIVERY_HEADER),
            event=headers.get(EVENT_HEADER),
            hook_id=headers.get(HOOK_ID_HEADER),
            hook_installation_target_id=headers.get(HOOK_INSTALLATION_TARGET_ID_HEADER),
            hook_installation_target_type=headers.get(
                HOOK_INSTALLATION_TARGET_TYPE_HEADER
            ),
            enterprise_version=headers.get(ENTERPRISE_VERSION_HEADER),
            enterprise_host=headers.get(ENTERPRISE_HOST_HEADER),
            user_id=user_id,
        )


class WebhookEvent(models.Model):
    payload = models.JSONField()
    delivery: models.CharField = models.CharField(max_length=255)
    event: models.CharField = models.CharField(max_length=255)
    hook_id: models.IntegerField = models.IntegerField()
    hook_installation_target_id: models.IntegerField = models.IntegerField()
    hook_installation_target_type: models.CharField = models.CharField(max_length=255)
    enterprise_version: models.CharField = models.CharField(max_length=255, null=True)
    enterprise_host: models.CharField = models.CharField(max_length=255, null=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    processed_at: models.DateTimeField = models.DateTimeField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    installation = models.ForeignKey(
        Installation, on_delete=models.CASCADE, null=True, related_name="webhook_events"
    )

    objects = WebhookEventManager()

    def __str__(self):
        return f"{self.hook_id} - {self.delivery}"

    @property
    def is_processable_webhook_event(self) -> bool:
        action = self.payload.get("action")
        is_completed = action == "completed"
        event_type = self.event
        is_workflow_related = event_type in ["workflow_run", "workflow_job"]
        return is_completed and is_workflow_related

    def associate_installation(self) -> Installation:
        installation_data = self.payload.get("installation")
        if installation_data:
            installation_id = installation_data.get("id")
            installation, _ = Installation.objects.get_or_create(
                enterprise_host=self.enterprise_host,
                installation_id=installation_id,
                is_artificial=False,
            )
        else:
            installation = Installation.objects.get_or_create_artificial_installation(
                enterprise_host=self.enterprise_host,
                webhook_id=self.hook_id,
            )
        self.installation = installation
        if self.user:
            self.installation.users.add(self.user)
        return installation

    def save(self, *args, **kwargs):
        self.associate_installation()
        super().save(*args, **kwargs)
