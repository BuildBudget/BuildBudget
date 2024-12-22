from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from actions_data.models import UserProfile


class AdminTests(TestCase):
    fixtures = [
        "tests/fixtures/authusers.yaml",
        "tests/fixtures/usersocialauths.yaml",
        "tests/fixtures/ownerentities.yaml",
        "tests/fixtures/repositories.yaml",
        "tests/fixtures/webhook_events.yaml",
    ]

    def setUp(self):
        # Create superuser
        self.admin_user = User.objects.create_superuser(
            username="testadmin7", email="admin@example.com", password="adminpass123"
        )
        self.profile = UserProfile.objects.filter(user_id=34).first()
        self.client = Client()
        self.client.login(username="testadmin7", password="adminpass123")

    def test_owner_entity_admin(self):
        url = reverse("admin:actions_data_ownerentity_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kubernetes")

    def test_webhook_event_admin(self):
        url = reverse("admin:actions_data_webhookevent_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "workflow_run")

        # Test webhook event detail view
        url = reverse("admin:actions_data_webhookevent_change", args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sender")

    def test_user_profile_admin(self):
        url = reverse("admin:actions_data_userprofile_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "eduramirezh")

        # Test user profile detail view
        url = reverse("admin:actions_data_userprofile_change", args=[self.profile.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "eduramirezh")

    def test_user_profile_github_connection(self):
        url = reverse("admin:actions_data_userprofile_change", args=[self.profile.pk])
        response = self.client.get(url)

        # Test GitHub connection status
        self.assertContains(response, "GitHub Connection Details")
        self.assertContains(response, "Username: eduramirez")

        # Delete social auth and test disconnected state
        self.profile.user.social_auth.all().delete()
        response = self.client.get(url)
        self.assertContains(response, "No GitHub account connected")

    def test_repository_count_annotation(self):
        # Create additional repository for testing count
        url = reverse("admin:actions_data_ownerentity_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # The owner should show 2 repositories
        self.assertContains(response, "actions-insider")
        self.assertContains(response, "2")  # Repository count
