# Generated by Django 5.1 on 2024-10-15 11:15

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("actions_data", "0037_alter_membership_auth_user_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="membership",
            name="user",
        ),
        migrations.RemoveField(
            model_name="ownerentity",
            name="members",
        ),
        migrations.RemoveField(
            model_name="repository",
            name="allowed_access",
        ),
        migrations.AlterUniqueTogether(
            name="repositoryaccess",
            unique_together={("auth_user", "repository")},
        ),
        migrations.RemoveField(
            model_name="repositoryaccess",
            name="user",
        ),
    ]
