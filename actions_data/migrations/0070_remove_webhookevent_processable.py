# Generated by Django 5.1 on 2024-11-08 11:22

from django.db import migrations
from django.db.migrations import RunPython


def delete_non_processable_webhook_events(apps, schema_editor):
    WebhookEvent = apps.get_model("actions_data", "WebhookEvent")
    deleted_counts = WebhookEvent.objects.filter(processable=False).delete()
    print(f"Deleted {deleted_counts[0]} non-processable webhook events.")


class Migration(migrations.Migration):

    dependencies = [
        (
            "actions_data",
            "0069_remove_runnercostconfig_infrastructure_cost_per_hour_and_more",
        ),
    ]

    operations = [
        RunPython(
            code=delete_non_processable_webhook_events,
            reverse_code=migrations.RunPython.noop,
        )
    ]
