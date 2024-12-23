# Generated by Django 5.1 on 2024-10-18 13:41
import math
from datetime import timedelta

from django.db import migrations


def populate_job_stats(apps, schema_editor):
    JobStats = apps.get_model("actions_data", "JobStats")
    Job = apps.get_model("actions_data", "Job")
    job_count = Job.objects.count()
    i = 0
    for job in Job.objects.all():
        i += 1
        print(f"Processing job {i}/{job_count}")
        if (
            not job.workflow_run
            or not job.workflow_run.workflow
            or not job.started_at
            or not job.completed_at
        ):
            continue

        execution_time = job.completed_at - job.started_at
        billable_time = timedelta(
            minutes=max(1, math.ceil(execution_time.total_seconds() / 60))
        )

        JobStats.objects.update_or_create(
            job_id=job.id,
            defaults={
                "workflow_run": job.workflow_run,
                "workflow": job.workflow_run.workflow,
                "repository": job.workflow_run.repository,
                "owner_entity": job.workflow_run.repository.owner,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "execution_time": execution_time,
                "billable_time": billable_time,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "actions_data",
            "0047_jobstats_remove_job_actions_dat_started_3bf537_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            # Bypassing because Heroku doesn't run this properly. Using the populate_job_stats command instead
            migrations.RunPython.noop,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
