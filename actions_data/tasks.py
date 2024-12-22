import logging
from datetime import timedelta

import redis
import requests_cache
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from requests_cache import RedisCache

from actions_data.models import OwnerEntity
from actions_data.models.webhook_event import WebhookEvent
from actions_data.operations.demo_data_pusher import (
    DemoDataPusher,
    link_demo_repos_to_demo_user,
)
from actions_data.operations.webhook_processor import process_webhook_event_instance

logger = logging.getLogger("celery")


@shared_task
def process_webhook_event(event_id: int):
    logger.debug(f"Processing webhook event with id: {event_id}")
    wh_event = WebhookEvent.objects.get(id=event_id)
    process_webhook_event_instance(wh_event)


@shared_task(time_limit=5700)
def process_organization_data(org_id: int, started_minutes_ago: int):
    """Process GitHub data for a single organization."""
    connection = redis.from_url(settings.CELERY_BROKER_URL, ssl_cert_reqs=None)
    backend = RedisCache(connection=connection)
    requests_cache.install_cache(cache_control=True, backend=backend)
    started_time_ago = timedelta(minutes=started_minutes_ago)
    org = OwnerEntity.objects.get(id=org_id)

    logger.info(f"Processing data for organization: {org.login}")

    pusher = DemoDataPusher(webhook_processing_function=process_webhook_event)
    client_org, repositories = pusher.get_selected_repos_for_org(org)

    for repo in repositories:  # Keep the 50 repos limit
        pusher.process_repo(client_org, repo, timezone.now() - started_time_ago)

    logger.info(
        f"Completed processing data for organization: {org.login}. Total repos processed: {len(repositories)}"
    )
    requests_cache.uninstall_cache()
    connection.close()


@shared_task
def link_demo_repos():
    link_demo_repos_to_demo_user()


@shared_task(time_limit=5700)
def push_demo_data_to_webhook_events(started_minutes_ago: int):
    """
    Dispatches parallel tasks to process each organization's data.
    Each organization is processed in its own Celery task.
    """
    logger.info("Starting parallel processing of demo data")

    # Get all organizations marked for API fetching
    orgs = OwnerEntity.objects.filter(fetch_from_api=True)

    if not orgs.exists():
        logger.warning("No organizations marked for API fetching found")
        return

    # Launch a separate task for each organization
    for org in orgs:
        logger.info(f"Dispatching task for organization: {org.login}")
        process_organization_data.delay(org.id, started_minutes_ago)

    logger.info(f"Dispatched processing tasks for {orgs.count()} organizations")
