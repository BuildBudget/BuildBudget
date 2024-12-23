# Generated by Django 5.1.3 on 2024-12-12 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0090_jobstats_actions_dat_owner_e_ca201c_idx_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="jobstats",
            index=models.Index(
                fields=["workflow_id", "owner_entity_id"],
                name="actions_dat_workflo_352087_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="runnerlabelmultiplier",
            index=models.Index(
                fields=["label", "-per_minute_rate"],
                name="actions_dat_label_17b3f9_idx",
            ),
        ),
    ]
