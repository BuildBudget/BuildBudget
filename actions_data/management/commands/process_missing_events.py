from django.core.management import BaseCommand

from actions_data.models import WebhookEvent
from actions_data.operations.webhook_processor import process_webhook_event_instance


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=10000,
            help="Max number of webhook events to process",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        # Get all unprocessed webhook events respecting the limit
        unprocessed_webhook_events = WebhookEvent.objects.filter(processed_at=None)[
            :limit
        ]
        if len(unprocessed_webhook_events) == 0:
            self.stdout.write("No unprocessed webhook events found.")
        for event in unprocessed_webhook_events:
            try:
                process_webhook_event_instance(event)
            except Exception as e:
                self.stdout.write(
                    f"Failed to process webhook event: {event}. Error: {e}"
                )
