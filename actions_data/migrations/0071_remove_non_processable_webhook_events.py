# Generated by Django 5.1 on 2024-11-08 11:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0070_remove_webhookevent_processable"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="webhookevent",
            name="processable",
        ),
    ]
