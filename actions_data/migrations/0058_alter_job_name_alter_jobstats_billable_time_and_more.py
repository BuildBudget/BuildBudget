# Generated by Django 5.1 on 2024-10-31 16:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0057_jobstats_unique_job_stats_for_job"),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="name",
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name="jobstats",
            name="billable_time",
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
        migrations.AlterField(
            model_name="jobstats",
            name="execution_time",
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
    ]
