# Generated by Django 5.1 on 2024-09-13 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0016_repository_last_webhook_received_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ownerentity",
            name="webhook_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
