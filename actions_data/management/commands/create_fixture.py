from django.core.management import BaseCommand

from actions_data.models import JobStats
from tests.conftest import serialize_collection


class Command(BaseCommand):
    help = "Create a fixture from the database"

    def handle(self, *args, **options):
        js = JobStats.objects.filter(
            repository_id=259445878, workflow_run_id=27261
        ).select_related("job")
        jobs = [j.job for j in js]
        wf_runs = [j.workflow_run for j in js]
        wfs = [j.workflow for j in js]
        repository = js[0].repository
        oe = repository.owner

        serialize_collection([oe], "owner_entity.yaml")
