from django.core.management.base import BaseCommand
from actions_data.models import JobStats, Installation


class Command(BaseCommand):
    help = "Link demo Job stats to the demo installation"

    def handle(self, *args, **kwargs):
        demo_installation = Installation.objects.demo_installation()
        updated = JobStats.objects.filter(owner_entity__fetch_from_api=True).update(
            installation=demo_installation
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully linked {updated} JobStats entries to the demo installation."
            )
        )
