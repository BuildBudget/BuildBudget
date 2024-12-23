# Generated by Django 5.1.3 on 2024-11-29 20:51

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0078_job_idx_job_labels_gin_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddIndex(
            model_name="jobstats",
            index=models.Index(
                fields=["installation_id", "started_at"],
                name="actions_dat_install_78b511_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ownerentity",
            index=models.Index(fields=["login"], name="actions_dat_login_7bf484_idx"),
        ),
        migrations.AddIndex(
            model_name="repository",
            index=models.Index(fields=["name"], name="actions_dat_name_b520b3_idx"),
        ),
        migrations.AddIndex(
            model_name="workflow",
            index=models.Index(fields=["name"], name="actions_dat_name_9f60f4_idx"),
        ),
    ]
