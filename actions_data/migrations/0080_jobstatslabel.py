# Generated by Django 5.1.3 on 2024-11-30 19:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0079_jobstats_actions_dat_install_78b511_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobStatsLabel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.CharField(max_length=255)),
                (
                    "job_stats",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="labels",
                        to="actions_data.jobstats",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["job_stats_id"], name="actions_dat_job_sta_b67e6d_idx"
                    )
                ],
                "unique_together": {("job_stats", "label")},
            },
        ),
    ]
