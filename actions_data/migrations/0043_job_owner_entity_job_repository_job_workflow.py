# Generated by Django 5.1 on 2024-10-17 15:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0042_job_actions_dat_started_8146f7_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="owner_entity",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="actions_data.ownerentity",
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="repository",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="actions_data.repository",
            ),
        ),
        migrations.AddField(
            model_name="job",
            name="workflow",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="actions_data.workflow",
            ),
        ),
    ]
