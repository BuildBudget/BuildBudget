from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Min
from django.utils.timezone import now

from actions_data.models import JobStats  # Adjust import path as needed


class Command(BaseCommand):
    help = "Populates name fields in JobStats table using related object names"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50000,
            help="Number of records to update in each batch",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

        # Get total count for progress reporting
        total_records = JobStats.objects.count()
        self.stdout.write(f"Starting to update {total_records} JobStats records...")
        start_time = now()

        # PostgreSQL-specific UPDATE FROM query
        update_query = """
            UPDATE actions_data_jobstats js
            SET
                job_name = j.name,
                workflow_name = w.name,
                repository_name = r.name,
                owner_entity_name = oe.login
            FROM
                actions_data_job j,
                actions_data_workflow w,
                actions_data_repository r,
                actions_data_ownerentity oe
            WHERE
                js.id >= %s AND js.id < %s
                AND js.job_id = j.id
                AND js.workflow_id = w.id
                AND js.repository_id = r.id
                AND js.owner_entity_id = oe.id
        """

        # Get the range of IDs
        min_id = JobStats.objects.aggregate(Min("id"))["id__min"]
        if min_id is None:
            self.stdout.write("No records found to update.")
            return

        current_id = min_id
        updated_total = 0

        with connection.cursor() as cursor:
            while True:
                # Update batch
                cursor.execute(update_query, [current_id, current_id + batch_size])
                rows_updated = cursor.rowcount

                if rows_updated == 0:
                    break

                updated_total += rows_updated
                current_id += batch_size

                # Progress reporting
                progress = (updated_total / total_records) * 100
                elapsed = now() - start_time
                self.stdout.write(
                    f"Updated {updated_total:,} of {total_records:,} records "
                    f"({progress:.1f}%) in {elapsed}"
                )

        # Verify results
        null_names = JobStats.objects.filter(
            job_name__isnull=True,
            workflow_name__isnull=True,
            repository_name__isnull=True,
            owner_entity_name__isnull=True,
        ).count()

        total_time = now() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed! Updated {updated_total:,} records in {total_time}\n"
                f"Average speed: {updated_total / total_time.total_seconds():.1f} records/second"
            )
        )

        if null_names > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Found {null_names:,} records with null name fields after update"
                )
            )
