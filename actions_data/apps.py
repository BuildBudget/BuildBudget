from django.apps import AppConfig

from actions_insider.middleware import check_field_limits


class ActionsDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "actions_data"

    def ready(self):
        # Import the signal receiver here to avoid AppRegistryNotReady error
        import sys

        if "migrate" not in sys.argv and "makemigrations" not in sys.argv:
            from django.db.models.signals import pre_save

            pre_save.connect(check_field_limits)
