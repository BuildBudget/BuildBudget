# Generated by Django 5.1 on 2024-09-13 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0015_membership_ownerentity_members"),
    ]

    operations = [
        migrations.AddField(
            model_name="repository",
            name="last_webhook_received",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="repository",
            name="webhook_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
