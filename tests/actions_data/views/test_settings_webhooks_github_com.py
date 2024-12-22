import datetime

import responses
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class GithubComSettingsViewTests(TestCase):
    """Tests for the main GitHub settings view."""

    fixtures = ["tests/fixtures/authusers.yaml", "tests/fixtures/usersocialauths.yaml"]

    def setUp(self):
        self.user = User.objects.get(id=34)
        self.user_profile = self.user.userprofile
        self.client.force_login(self.user)
        self.url = reverse("settings")

    def test_unauthenticated_access(self):
        """Test that unauthenticated users are redirected to login."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    @responses.activate
    def test_get_context_data(self):
        """Test that the main view renders correctly with minimal context."""
        responses._add_from_file(file_path="tests/responses/test_get_context_data.yaml")
        # Create some artificial installations

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "actions_data/settings.html")

        # Check that loading state elements are present
        self.assertInHTML(
            "actions-insider",
            response.content.decode(),
        )

        self.assertEqual(len(self.user.installations.all()), 4)
        installation = self.user.installations.order_by("installation_id").first()
        # assert all ExtendedInstallation properties are present
        self.assertEqual(installation.app_slug, "buildbudget-dev")
        self.assertEqual(installation.client_id, "Iv23liH7z5jh4CGvZtxk")
        self.assertEqual(
            installation.access_tokens_url,
            "https://api.github.com/app/installations/56709260/access_tokens",
        )
        self.assertEqual(
            installation.html_url, "https://github.com/settings/installations/56709260"
        )
        self.assertEqual(
            installation.repositories_url,
            "https://api.github.com/installation/repositories",
        )
        self.assertEqual(installation.repository_selection, "all")
        self.assertEqual(installation.has_multiple_single_files, False)
        self.assertEqual(installation.single_file_name, None)
        self.assertEqual(installation.single_file_paths, [])
        self.assertEqual(installation.events, ["workflow_job", "workflow_run"])
        self.assertEqual(
            installation.permissions,
            {
                "actions": "read",
                "deployments": "read",
                "environments": "read",
                "metadata": "read",
            },
        )
        self.assertEqual(
            installation.created_at,
            datetime.datetime(2024, 11, 3, 9, 6, 25, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            installation.updated_at,
            datetime.datetime(2024, 12, 1, 14, 3, 47, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(installation.suspended_at, None)
        self.assertEqual(installation.suspended_by, None)

    def test_no_github_account(self):
        """Test view rendering when user has no GitHub account connected."""
        # Remove GitHub social auth
        self.user.social_auth.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertInHTML("Connect GitHub Repos", response.content.decode())
