from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin
from social_django.models import UserSocialAuth
from django.db.models import Case, When, Value, BooleanField

from actions_data.models import (
    OwnerEntity,
    Repository,
    Workflow,
    WorkflowRun,
    Job,
    WebhookEvent,
    UserProfile,
    Installation,
)


class OwnerEntityAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("login", "repo_count", "fetch_from_api")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            repo_count=Count("repositories", distinct=True),
        )
        return queryset

    def repo_count(self, obj):
        return obj.repo_count

    repo_count.short_description = "Number of repos"
    repo_count.admin_order_field = "repo_count"


class InstallationAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "installation_id",
        "is_artificial",
        "enterprise_host",
        "created_at",
    )


admin.site.register(OwnerEntity, OwnerEntityAdmin)
admin.site.register(Repository)
admin.site.register(Workflow)
admin.site.register(WorkflowRun)
admin.site.register(Job)
admin.site.register(Installation, InstallationAdmin)


@admin.register(WebhookEvent)
class WebhookEventAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ("event", "created_at", "processed_at")
    list_filter = ("event", "created_at", "processed_at")
    search_fields = ("event", "delivery")
    readonly_fields = (
        "payload",
        "delivery",
        "event",
        "hook_id",
        "hook_installation_target_id",
        "hook_installation_target_type",
        "enterprise_version",
        "enterprise_host",
        "created_at",
    )


@admin.register(UserProfile)
class UserProfileAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "use_as_global_token",
        "webhook_secret",
        "is_github_connected",
        "github_username",
    )
    list_editable = ("use_as_global_token",)
    list_filter = ("use_as_global_token", "user__is_active")
    search_fields = ("user__username", "user__email", "webhook_secret")
    readonly_fields = ("github_connection_status", "webhook_configuration_status")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("user").annotate(
            has_github=Case(
                When(user__social_auth__provider="github-app", then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def is_github_connected(self, obj):
        return (
            hasattr(obj.user, "social_auth")
            and obj.user.social_auth.filter(provider="github-app").exists()
        )

    is_github_connected.short_description = "GitHub Connected"
    is_github_connected.boolean = True

    def github_username(self, obj):
        try:
            social_auth = obj.user.social_auth.get(provider="github-app")
            username = social_auth.extra_data.get("login", "N/A")
            return format_html('<span style="color: #333;">{}</span>', username)
        except UserSocialAuth.DoesNotExist:
            return format_html('<span style="color: #999;">Not connected</span>')

    github_username.short_description = "GitHub Username"

    def github_connection_status(self, obj):
        try:
            social_auth = obj.user.social_auth.get(provider="github-app")
            return format_html(
                '<div style="margin: 10px 0;">'
                "<strong>GitHub Connection Status:</strong><br>"
                "Username: {}<br>"
                "User ID: {}<br>"
                "Last Updated: {}"
                "</div>",
                social_auth.extra_data.get("login", "N/A"),
                social_auth.extra_data.get("id", "N/A"),
                social_auth.modified.strftime("%Y-%m-%d %H:%M:%S"),
            )
        except UserSocialAuth.DoesNotExist:
            return format_html(
                '<div style="color: red; margin: 10px 0;">'
                "No GitHub account connected"
                "</div>"
            )

    github_connection_status.short_description = "GitHub Connection Details"

    def webhook_configuration_status(self, obj):
        if obj.is_webhook_configured:
            webhooks_count = obj.user.webhooks.count()
            return format_html(
                '<div style="color: green; margin: 10px 0;">'
                "Webhooks configured: {}"
                "</div>",
                webhooks_count,
            )
        return format_html(
            '<div style="color: orange; margin: 10px 0;">'
            "No webhooks configured"
            "</div>"
        )

    webhook_configuration_status.short_description = "Webhook Configuration"

    fieldsets = (
        (
            "User Information",
            {"fields": ("user", "webhook_secret", "use_as_global_token")},
        ),
        (
            "GitHub Integration",
            {"fields": ("github_connection_status",), "classes": ("collapse",)},
        ),
        (
            "Webhook Information",
            {"fields": ("webhook_configuration_status",), "classes": ("collapse",)},
        ),
    )
