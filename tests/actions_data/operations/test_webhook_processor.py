from datetime import timedelta
from unittest import skipIf

from django.contrib.auth.models import User
from django.test import TestCase
from freezegun import freeze_time

from actions_data.models import WebhookEvent, WorkflowRun, Job
from actions_data.operations.schemas import OperationResult
from actions_data.operations.webhook_processor import (
    process_webhook_event_instance,
    process_workflow_run_event,
    process_workflow_job_event,
)


class TestWebhookProcessor(TestCase):

    fixtures = [
        "tests/fixtures/webhook_events.yaml",
        "tests/fixtures/authusers.yaml",
    ]

    def setUp(self):
        WorkflowRun.objects.all().delete()

    @freeze_time("2024-10-08")
    def test_process_workflow_run_event_success(self):
        event = WebhookEvent.objects.get(id=1)
        user = User.objects.get(id=34)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)
        wf_run = WorkflowRun.objects.get(run_id=10905389638)
        self.assertEqual(wf_run.name, "Docker")
        self.assertEqual(wf_run.repository.name, "hello-world")
        self.assertEqual(wf_run.actor.login, "eduramirezh")
        self.assertEqual(wf_run.triggering_actor.login, "eduramirezh")
        self.assertEqual(wf_run.head_repository.name, "hello-world")
        self.assertEqual(wf_run.workflow.name, "Docker")
        self.assertEqual(str(event.processed_at), "2024-10-08 00:00:00+00:00")

    def test_process_workflow_run_twice(self):
        event = WebhookEvent.objects.get(id=1)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)
        wf_run = WorkflowRun.objects.get(run_id=10905389638)
        self.assertEqual(wf_run.name, "Docker")

    @freeze_time("2024-10-08")
    def test_process_workflow_job_event_before_wf_run(self):
        user = User.objects.get(id=34)
        event = WebhookEvent.objects.get(id=2)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)
        job = Job.objects.get(id=30264097335)
        self.assertEqual(job.name, "build")
        self.assertEqual(job.workflow_run.run_id, 10905389638)
        self.assertEqual(job.workflow_run.name, None)
        self.assertEqual(str(event.processed_at), "2024-10-08 00:00:00+00:00")

    def test_process_workflow_job_event_after_wf_run(self):
        event = WebhookEvent.objects.get(id=1)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)
        event = WebhookEvent.objects.get(id=2)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)
        job = Job.objects.get(id=30264097335)
        self.assertEqual(job.name, "build")
        self.assertEqual(job.workflow_run.run_id, 10905389638)
        self.assertEqual(job.workflow_run.name, "Docker")
        job_stats = job.stats.first()
        self.assertEqual(job_stats.workflow.name, "Docker")
        self.assertEqual(job_stats.repository.name, "hello-world")
        self.assertEqual(job_stats.owner_entity.login, "actions-insider")
        self.assertEqual(job_stats.started_at, job.started_at)
        self.assertEqual(job_stats.completed_at, job.completed_at)
        self.assertEqual(job_stats.execution_time, timedelta(seconds=32))
        self.assertEqual(job_stats.billable_time, timedelta(seconds=60))

    def test_process_failing_webhook_event(self):
        event = WebhookEvent.objects.get(id=3)
        result = process_webhook_event_instance(event)
        self.assertEqual(result, OperationResult.SUCCESS)

    def test_process_webhook_event_over_dst(self):
        run_event = WebhookEvent.objects.get(id=3)
        job_event = WebhookEvent.objects.get(id=4)
        run_result = process_webhook_event_instance(run_event)
        job_result = process_webhook_event_instance(job_event)
        self.assertEqual(run_result, OperationResult.SUCCESS)
        self.assertEqual(job_result, OperationResult.SUCCESS)

    def test_process_workflow_run_event_failure(self):
        event = WebhookEvent.objects.get(id=1)
        event.payload = {"repository": {"name": "hello-world"}}
        event.save()
        self.assertEqual(process_workflow_run_event(event), OperationResult.FAILURE)

    def test_process_workflow_job_event_failure(self):
        event = WebhookEvent.objects.get(id=2)
        event.payload = {"repository": {"name": "hello-world"}}
        event.save()
        self.assertEqual(process_workflow_job_event(event), OperationResult.FAILURE)

    def test_process_webhook_event_instance_noop(self):
        event = WebhookEvent.objects.get(id=1)
        event.event = "workflow_jam"
        event.save()
        self.assertEqual(process_webhook_event_instance(event), OperationResult.NOOP)
