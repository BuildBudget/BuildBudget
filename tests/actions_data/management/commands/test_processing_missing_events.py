from unittest.mock import patch
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from actions_data.models import WebhookEvent


class ProcessWebhookEventsCommandTest(TestCase):

    fixtures = ["tests/fixtures/webhook_events.yaml"]

    @patch(
        "actions_data.management.commands.process_missing_events.process_webhook_event_instance"
    )
    def test_command_processes_unprocessed_events(self, mock_process):
        """
        Test that the command processes only unprocessed webhook events
        """
        # Call the command
        call_command("process_missing_events")

        # Assert process_webhook_event_instance was called for each unprocessed event
        self.assertEqual(mock_process.call_count, 3)

    @patch(
        "actions_data.management.commands.process_missing_events.process_webhook_event_instance"
    )
    def test_command_handles_empty_queue(self, mock_process):
        """
        Test that the command handles the case when there are no unprocessed events
        """
        # Mark all events as processed
        WebhookEvent.objects.all().update(processed_at=timezone.now())

        # Call the command
        call_command("process_missing_events")

        # Assert process_webhook_event_instance was not called
        mock_process.assert_not_called()

    @patch(
        "actions_data.management.commands.process_missing_events.process_webhook_event_instance"
    )
    def test_command_handles_processing_error(self, mock_process):
        """
        Test that the command continues processing remaining events even if one fails
        """
        # Make the first event processing raise an exception
        mock_process.side_effect = [Exception("Processing failed"), None]

        # Call the command
        call_command("process_missing_events")

        # Assert second event was still processed despite first one failing
        self.assertEqual(mock_process.call_count, 3)

    @patch(
        "actions_data.management.commands.process_missing_events.process_webhook_event_instance"
    )
    def test_respects_limit(self, mock_process):
        """
        Test that the command respects the limit argument
        """
        # Call the command with a limit of 1
        call_command("process_missing_events", limit=1)

        # Assert process_webhook_event_instance was called only once
        mock_process.assert_called_once()
        self.assertEqual(mock_process.call_count, 1)
