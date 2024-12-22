import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils.http import urlencode
from django.utils.timezone import now
from social_django.models import UserSocialAuth
from actions_data.models import (
    WebhookEvent,
    JobStats,
    Installation,
    Repository,
)


class TestViews(TestCase):
    fixtures = [
        "tests/fixtures/authusers.yaml",
        "tests/fixtures/usersocialauths.yaml",
        "tests/fixtures/owner_entity.yaml",
        "tests/fixtures/repository.yaml",
        "tests/fixtures/wfs.yaml",
        "tests/fixtures/wf_runs.yaml",
        "tests/fixtures/webhook_events.yaml",
        "tests/fixtures/jobs.yaml",
        "tests/fixtures/job_stats.yaml",
    ]

    def setUp(self):
        self.client = Client()
        self.social_user = UserSocialAuth.objects.get(id=1)
        self.user_without_github_data = User.objects.get(id=4)
        self.demo_user = User.objects.get(username=settings.DEMO_USERNAME)
        self.job_stats = JobStats.objects.all()
        for js in self.job_stats:
            js.completed_at = now()
            js.started_at = js.completed_at - js.execution_time
            js.save()

        repositories = Repository.objects.all()
        for repo in repositories:
            self.demo_user.userprofile.repositories.add(repo)
            self.social_user.user.userprofile.repositories.add(repo)

    def test_landing_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="mailto:contact@buildbudget.dev"')

    def test_logout(self):
        response = self.client.post("/logout/")
        self.assertRedirects(response, "/")

    def test_webhook(self):
        with open("tests/resources/sample_webhook_payload.json") as f:
            sample_webhook_payload = f.read()
        with open("tests/resources/sample_webhook_headers.json") as f:
            headers = json.load(f)

        response = self.client.post(
            "/webhook?user=2",
            data=sample_webhook_payload,
            headers=headers,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "")
        delivery_header = headers.get("X-GitHub-Delivery")
        saved_webhook = WebhookEvent.objects.get(delivery=delivery_header)
        self.assertEqual(saved_webhook.payload, json.loads(sample_webhook_payload))
        user = User.objects.get(id=2)
        self.assertEqual(saved_webhook.user_id, 2)

    def test_stats_pages_unauthenticated(self):
        stats_urls = [
            "/stats/by-job/",
            "/stats/by-workflow/",
            "/stats/by-repo/",
            "/stats/by-org/",
            "/stats/by-labels/",
        ]
        query_params = [
            "date_filter=past_day",
            "date_filter=past_week",
            "date_filter=past_month",
        ]
        subtests_urls = (
            f"{url}?{query}" for url in stats_urls for query in query_params
        )
        for url in subtests_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    "/login/github-app/?" + urlencode({"next": url}),
                    target_status_code=302,
                )

    def test_stats_pages_authenticated(self):
        stats_urls = [
            "/stats/by-job/",
            "/stats/by-workflow/",
            "/stats/by-repo/",
            "/stats/by-org/",
            "/stats/by-labels/",
        ]
        query_params = [
            "date_filter=past_day",
            "date_filter=past_week",
            "date_filter=past_month",
        ]
        subtests_urls = (
            f"{url}?{query}" for url in stats_urls for query in query_params
        )
        self.client.force_login(self.social_user.user)
        for url in subtests_urls:
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response, '<div id="statsChart" style="width: 100%;"></div>'
                )

    def test_demo_stats_pages(self):
        demo_urls = [
            "/demo/stats/by-job/",
            "/demo/stats/by-workflow/",
            "/demo/stats/by-repo/",
            "/demo/stats/by-org/",
            "/demo/stats/by-labels/",
        ]
        query_params = [
            "date_filter=past_day",
            "date_filter=past_week",
            "date_filter=past_month",
        ]
        subtests_urls = (
            f"{url}?{query}" for url in demo_urls for query in query_params
        )
        for url in subtests_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response, '<div id="statsChart" style="width: 100%;"></div>'
                )

    def test_redirected_from_landing_page_when_authenticated(self):
        self.client.force_login(self.social_user.user)
        response = self.client.get("/")
        self.assertRedirects(response, "/stats/by-workflow/")
