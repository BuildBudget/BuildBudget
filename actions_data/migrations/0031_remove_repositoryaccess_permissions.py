# Generated by Django 5.1 on 2024-10-02 15:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "actions_data",
            "0030_repositoryaccess_admin_repositoryaccess_maintain_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="repositoryaccess",
            name="permissions",
        ),
    ]
