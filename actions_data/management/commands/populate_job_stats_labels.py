from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from actions_data.models import JobStats, JobStatsLabel


class Command(BaseCommand):
    help = "Populates JobStatsLabel table based on existing Job labels"

    def handle(self, *args, **options):

        # Get total count for progress bar
        total_count = JobStats.objects.filter(
            job__labels__isnull=False, labels__isnull=True
        ).count()

        self.stdout.write(f"Processing {total_count} JobStats entries...")

        # Process in batches
        processed = 0
        created_labels = 0

        batch = JobStats.objects.select_related("job").filter(
            job__labels__isnull=False,
            labels__isnull=True,
        )

        # Create JobStatsLabel entries for this batch
        new_labels = []
        for job_stats in batch:
            if not isinstance(job_stats.job.labels, list):
                continue

            for label in job_stats.job.labels:
                if not isinstance(label, str):
                    continue

                new_labels.append(JobStatsLabel(job_stats=job_stats, label=label))

        # Bulk create the new labels, ignoring any duplicates
        if new_labels:
            created = len(JobStatsLabel.objects.bulk_create(new_labels))
            created_labels += created

        # Update progress
        batch_count = len(batch)
        processed += batch_count

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {processed} JobStats entries and created {created_labels} labels"
            )
        )
