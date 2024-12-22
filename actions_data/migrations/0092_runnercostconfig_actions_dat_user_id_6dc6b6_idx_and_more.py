# Generated by Django 5.1.3 on 2024-12-12 14:40

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0091_jobstats_actions_dat_workflo_352087_idx_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name="runnercostconfig",
            index=models.Index(
                fields=["user_id"], name="actions_dat_user_id_6dc6b6_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="runnerlabelmultiplier",
            index=models.Index(
                fields=["label", "cost_config_id", "-per_minute_rate"],
                name="actions_dat_label_5d8750_idx",
            ),
        ),
    ]
