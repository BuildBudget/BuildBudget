import logging

from django.core.exceptions import ValidationError
from django.utils.timezone import now

from actions_data.models import WebhookEvent, Job, WorkflowRun
from actions_data.operations.schemas import OperationResult

logger = logging.getLogger("celery")


def process_workflow_run_event(event: WebhookEvent) -> OperationResult:
    try:
        result = WorkflowRun.objects.get_or_create_from_webhook_event(event)
        logger.debug(f"Successfully processed workflow run event: {result}")
        event.processed_at = now()
        event.save()
        return OperationResult.SUCCESS
    except Exception as e:
        logger.exception(
            f"Failed to process workflow run event: {event}. Exception: {e}",
            exc_info=True,
        )
        return OperationResult.FAILURE


def process_workflow_job_event(event: WebhookEvent) -> OperationResult:
    try:
        result = Job.objects.get_or_create_from_webhook_event(event)
        logger.debug(f"Successfully processed workflow job event: {result}")
        event.processed_at = now()
        event.save()
        return OperationResult.SUCCESS
    except ValidationError as e:
        if "Job stats with this Job already exists" in str(e):
            logger.info(f"JobStat already exists for the job in this event: {event}")
            return OperationResult.NOOP
        logger.exception(
            f"Failed to process workflow job event: {event}. Exception: {e}",
            exc_info=True,
        )
    except Exception as e:
        logger.exception(
            f"Failed to process workflow job event: {event}. Exception: {e}",
            exc_info=True,
        )
    return OperationResult.FAILURE


def process_webhook_event_instance(event: WebhookEvent) -> OperationResult:
    if event.is_processable_webhook_event:
        match event.event:
            case "workflow_run":
                return process_workflow_run_event(event)
            case "workflow_job":
                return process_workflow_job_event(event)
            case _:
                raise ValueError(
                    f"Unexpectedly processing unsupported event type: {event.event}"
                )
    else:
        logger.debug(f"Deleting non processable event: {event}")
        event.delete()
        return OperationResult.NOOP
