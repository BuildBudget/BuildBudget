from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Populates event field in JobStats from associated WorkflowRuns"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get count of records that need updating
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM actions_data_jobstats
                WHERE event IS NULL
            """
            )
            count = cursor.fetchone()[0]

            if count == 0:
                self.stdout.write(
                    self.style.SUCCESS("No JobStats records need updating")
                )
                return

            self.stdout.write(f"Updating {count} JobStats records...")

            # Update all records in a single query
            cursor.execute(
                """
                UPDATE actions_data_jobstats
                SET event = actions_data_workflowrun.event
                FROM actions_data_workflowrun
                WHERE actions_data_jobstats.workflow_run_id = actions_data_workflowrun.id
                AND actions_data_jobstats.event IS NULL
            """
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {cursor.rowcount} JobStats records"
                )
            )
