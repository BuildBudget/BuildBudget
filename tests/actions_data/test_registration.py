from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from actions_data.models import UserProfile


class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("signup")
        self.login_url = reverse("login")
        self.webhook_registration_url = reverse("settings_webhooks_github_es")
        self.stats_by_workflow_url = reverse("stats_by_workflow")
        self.user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password1": "complex_password123",
            "password2": "complex_password123",
        }

    def test_signup_page_loads(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_successful_signup(self):
        response = self.client.post(self.signup_url, self.user_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful signup
        self.assertRedirects(response, self.webhook_registration_url)
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertTrue(UserProfile.objects.filter(user__username="testuser").exists())

    def test_signup_with_invalid_data(self):
        invalid_data = self.user_data.copy()
        invalid_data["password2"] = "mismatched_password"
        response = self.client.post(self.signup_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Stay on the same page
        form = response.context["form"]
        self.assertFormError(form, "password2", "The two password fields didn’t match.")

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_successful_login(self):
        created_user = User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
        )
        created_user.set_password(self.user_data["password1"])
        created_user.save()
        response = self.client.post(
            self.login_url,
            {
                "username": created_user.username,
                "password": self.user_data["password1"],
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertRedirects(response, self.stats_by_workflow_url)

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "nonexistent_user",
                "password": "wrong_password",
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFormError(
            form,
            None,
            "Please enter a correct username and password. Note that both fields may be case-sensitive.",
        )
        self.assertContains(response, "Please enter a correct username and password.")
