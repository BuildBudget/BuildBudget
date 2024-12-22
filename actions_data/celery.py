import os

from celery import Celery
from celery.schedules import crontab
from celery.signals import beat_init

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "actions_insider.settings")

app = Celery("actions_data")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "push-demo-data-every-hour": {
        "task": "actions_data.tasks.push_demo_data_to_webhook_events",
        "schedule": crontab(minute="46"),
        "args": (70,),
    },
    "link-demo-repos-every-hour": {
        "task": "actions_data.tasks.link_demo_repos",
        "schedule": crontab(minute="17"),
    },
}


@beat_init.connect
def beat_init_handler(**kwargs):
    app.send_task("actions_data.tasks.push_demo_data_to_webhook_events", args=(65,))
