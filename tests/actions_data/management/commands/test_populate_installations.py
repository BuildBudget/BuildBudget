from django.core.management import call_command
from django.test import TestCase
from actions_data.models import JobStats, Installation


class LinkDemoJobStatsTestCase(TestCase):
    fixtures = [
        "tests/fixtures/authusers.yaml",
        "tests/fixtures/usersocialauths.yaml",
        "tests/fixtures/webhook_events.yaml",
        "tests/fixtures/owner_entity.yaml",
        "tests/fixtures/repository.yaml",
        "tests/fixtures/wfs.yaml",
        "tests/fixtures/wf_runs.yaml",
        "tests/fixtures/jobs.yaml",
        "tests/fixtures/job_stats.yaml",
    ]

    def setUp(self):
        self.demo_installation = Installation.objects.demo_installation()

    def test_link_demo_job_stats(self):
        jobstats_for_demo_installation = JobStats.objects.filter(
            installation=self.demo_installation
        )
        self.assertEqual(jobstats_for_demo_installation.count(), 0)

        call_command("populate_installations")

        self.assertEqual(jobstats_for_demo_installation.count(), 16)
