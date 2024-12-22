from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from actions_data.models import Installation


class GHESSettingsViewTests(TestCase):
    fixtures = ["tests/fixtures/authusers.yaml"]

    def setUp(self):
        self.user = User.objects.get(id=34)
        self.user_profile = self.user.userprofile
        self.client.force_login(self.user)

    def test_get_context_data(self):
        # Add artificial installations
        # Create some existing webhooks, avoiding demo webhook
        for i in range(3, 6):
            installation = Installation.objects.get_or_create_artificial_installation(
                enterprise_host=f"test{i}.com",
                webhook_id=i,
            )
            self.user.installations.add(installation)

        url = reverse(
            "settings_webhooks_github_es"
        )  # Make sure this matches your URL name
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("webhook_secret", response.context)
        self.assertIn("webhook_url", response.context)
        self.assertIn("existing_installations", response.context)
        self.assertEqual(len(response.context["existing_installations"]), 3)
        self.assertIn("current_timestamp", response.context)

    def test_unauthenticated_access(self):
        self.client.logout()
        url = reverse("settings_webhooks_github_es")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login page
