# Generated by Django 5.1 on 2024-10-21 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0049_webhookevent_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerentity",
            name="fetch_from_api",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="use_as_global_token",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="repositoryaccess",
            name="source",
            field=models.CharField(
                choices=[
                    ("GITHUB_API", "Github API"),
                    ("MANUAL", "Manual"),
                    ("WEBHOOK", "Webhook"),
                ],
                default="GITHUB_API",
                max_length=50,
            ),
        ),
    ]
