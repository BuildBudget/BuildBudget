from django.test import TestCase

from actions_data.models import Workflow, WorkflowRun, Job
from actions_data.tasks import (
    process_webhook_event,
)


class TestTasks(TestCase):

    fixtures = [
        "tests/fixtures/webhook_events.yaml",
    ]

    def test_process_webhook_event(self):
        process_webhook_event(event_id=1)
        wf_run = WorkflowRun.objects.get(run_id=10905389638)
        self.assertEqual(wf_run.name, "Docker")
        self.assertEqual(wf_run.repository.name, "hello-world")
        self.assertEqual(wf_run.actor.login, "eduramirezh")
        self.assertEqual(wf_run.triggering_actor.login, "eduramirezh")
        self.assertEqual(wf_run.head_repository.name, "hello-world")
        self.assertEqual(wf_run.workflow.name, "Docker")
