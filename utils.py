import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


def round_duration_to_seconds(duration: timedelta) -> timedelta:
    try:
        rounded_seconds = round(duration.total_seconds())
    except AttributeError as e:
        logger.warning(f"Failed to round duration to seconds: {e}")
        return timedelta(seconds=0)
    return timedelta(seconds=rounded_seconds)
