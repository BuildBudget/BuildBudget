from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView


class GithubESWebhookSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "actions_data/webhooks/github_es.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_profile = user.userprofile
        context["webhook_secret"] = user_profile.webhook_secret
        context["webhook_url"] = settings.WEBHOOK_URL + f"?user={self.request.user.id}"

        existing_installations = self.request.user.installations.all()
        if existing_installations.exists():
            context["existing_installations"] = [
                {
                    "webhook_id": installation.webhook_id,
                    "host": installation.enterprise_host,
                }
                for installation in existing_installations
            ]

        # Add current timestamp
        context["current_timestamp"] = timezone.now().isoformat()

        return context
