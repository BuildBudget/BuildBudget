from datetime import timedelta

from django.core.management import BaseCommand

from actions_data.operations.demo_data_pusher import DemoDataPusher
from actions_data.tasks import process_webhook_event


class Command(BaseCommand):
    help = "Push demo data to webhook events"

    def add_arguments(self, parser):
        parser.add_argument(
            "--started-minutes-ago",
            type=int,
            default=5,
            help="Number of minutes ago to start pushing demo data",
        )

    def handle(self, *args, **options):
        started_time_ago = timedelta(minutes=options["started_minutes_ago"])
        DemoDataPusher(
            webhook_processing_function=process_webhook_event
        ).push_demo_data_to_webhook_events(started_time_ago)
