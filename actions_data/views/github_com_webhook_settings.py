from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.views.generic import TemplateView

from actions_data.github_client import get_github_orgs_and_repos_with_app_installed


class GithubComWebhookSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "actions_data/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_profile = user.userprofile
        github_orgs = user_profile.update_github_orgs_and_repos_with_app_installed()
        context["github_orgs"] = github_orgs

        if user.social_auth.exists():
            context["github_account"] = user.social_auth.get(provider="github-app")
        context["github_app_url"] = settings.GITHUB_APP_URL
        return context
