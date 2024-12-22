from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from actions_data.models import Installation


class CheckWebhookStatusViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.user_profile = self.user.userprofile
        self.client.login(username="testuser", password="12345")

    def test_new_webhook_verification(self):
        reference_time = timezone.now()

        # Create a new installation for the user after the reference time
        new_installation = Installation.objects.get_or_create_artificial_installation(
            enterprise_host="github.com", webhook_id=12345
        )
        new_installation.users.add(self.user)
        new_installation.save()

        url = reverse("new_webhook_status")  # Make sure this matches your URL name
        response = self.client.get(url, {"reference_time": reference_time.isoformat()})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["verified"])
        self.assertEqual(data["new_webhook"]["webhook_id"], new_installation.webhook_id)

    def test_no_new_webhook(self):
        reference_time = timezone.now()

        url = reverse("new_webhook_status")
        response = self.client.get(url, {"reference_time": reference_time.isoformat()})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["verified"])
        self.assertIsNone(data["new_webhook"])

    def test_missing_reference_time(self):
        url = reverse("new_webhook_status")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_invalid_reference_time(self):
        url = reverse("new_webhook_status")
        response = self.client.get(url, {"reference_time": "invalid_time"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_unauthenticated_access(self):
        self.client.logout()
        url = reverse("new_webhook_status")
        response = self.client.get(url, {"reference_time": timezone.now().isoformat()})
        self.assertEqual(response.status_code, 302)  # Should redirect to login page
