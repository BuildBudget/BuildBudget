# Generated by Django 5.1 on 2024-09-06 15:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0014_remove_job_workflow_run_attempt_and_more"),
        ("social_django", "0016_alter_usersocialauth_extra_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="Membership",
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
                (
                    "state",
                    models.CharField(
                        choices=[("active", "Active"), ("pending", "Pending")],
                        max_length=50,
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[("admin", "Admin"), ("member", "Member")],
                        max_length=50,
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="actions_data.ownerentity",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="social_django.usersocialauth",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="ownerentity",
            name="members",
            field=models.ManyToManyField(
                related_name="organizations",
                through="actions_data.Membership",
                to="social_django.usersocialauth",
            ),
        ),
    ]
