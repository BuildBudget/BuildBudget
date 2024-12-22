from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

from actions_data.models import RunnerLabelMultiplier


class LabelManagementViewTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        # Create cost config for the user
        self.cost_config = self.user.runner_cost_config
        self.cost_config.save()

        # URL for the view
        self.url = reverse("label_management")

    def test_login_required(self):
        """Test that view requires login"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/github-app"))

    def test_get_view_no_labels(self):
        """Test GET request when no labels exist"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "actions_data/label_management.html")
        self.assertIsNone(response.context["formset"])

    def test_update_label_rate(self):
        """Test updating a label's per-minute rate"""
        # Create a label multiplier
        label_multiplier = RunnerLabelMultiplier.objects.create(
            cost_config=self.cost_config,
            label="ubuntu-latest",
            per_minute_rate=Decimal("0.0100"),
        )

        new_rate = "0.0200"
        response = self.client.post(
            self.url,
            {
                "form_type": "label",
                "label": "ubuntu-latest",
                "per_minute_rate": new_rate,
            },
        )

        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]), "Label 'ubuntu-latest' updated successfully!"
        )

        # Verify database update
        label_multiplier.refresh_from_db()
        self.assertEqual(label_multiplier.per_minute_rate, Decimal(new_rate))
