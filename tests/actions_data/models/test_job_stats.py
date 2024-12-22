from datetime import timedelta

from django.test import TestCase

from actions_data.models import Job


class JobStatsTest(TestCase):

    fixtures = [
        "tests/fixtures/owner_entity.yaml",
        "tests/fixtures/repository.yaml",
        "tests/fixtures/wfs.yaml",
        "tests/fixtures/wf_runs.yaml",
        "tests/fixtures/webhook_events.yaml",
        "tests/fixtures/jobs.yaml",
    ]

    def test_generated_job_stats(self):
        job = Job.objects.first()
        job_stats = job.save_job_stats_entry()
        self.assertEqual(job_stats.started_at, job.started_at)
        self.assertEqual(job_stats.completed_at, job.completed_at)
        self.assertEqual(job_stats.execution_time, timedelta(seconds=89))
        self.assertEqual(job_stats.billable_time, timedelta(minutes=2))

    def test_generated_job_stats_with_tolerance(self):
        job = Job.objects.first()
        job.started_at = job.completed_at + timedelta(seconds=1)
        job.save()
        job_stats = job.save_job_stats_entry()
        self.assertEqual(job_stats.started_at, job_stats.completed_at)
        self.assertEqual(job_stats.execution_time, timedelta(0))
        self.assertEqual(job_stats.billable_time, timedelta(minutes=1))
