import enum
from dataclasses import dataclass
from datetime import timedelta, datetime
from decimal import Decimal
from typing import Optional

from django.db import models
from django.utils import timezone


class DateFilterOptions(enum.Enum):
    PAST_DAY = "past_day"
    PAST_WEEK = "past_week"
    PAST_MONTH = "past_month"

    def _get_timedelta(self):
        return {
            self.PAST_DAY: timedelta(days=1),
            self.PAST_WEEK: timedelta(weeks=1),
            self.PAST_MONTH: timedelta(weeks=4),
        }[self]

    @property
    def start_date(self):
        delta = self._get_timedelta()
        if delta is None:
            return None
        return timezone.now() - delta


class ChartType(enum.Enum):
    JOB = "job"
    WORKFLOW = "workflow"
    REPO = "repo"
    ORG = "org"
    LABELS = "labels"


@dataclass
class AccumulatedMetricsResult:
    entity_id: Optional[str]
    name: str
    sum_execution_time: timedelta
    sum_billable_time: timedelta
    total_cost: Decimal
    url: str = ""


@dataclass
class TotalMetricsResult:
    total_execution_time: timedelta
    total_billable_time: timedelta
    total_cost: Decimal


@dataclass
class DateFilter:
    start_date: datetime.date
