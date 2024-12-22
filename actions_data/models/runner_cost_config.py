from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import (
    Value,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
    Count,
    Avg,
    QuerySet,
    Subquery,
    OuterRef,
    Max,
    Case,
    When,
)
from django.db.models.functions import Extract, TruncDate, Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver

from actions_data.models import JobStats, WorkflowRun
from utils import round_duration_to_seconds


class WorkflowCostCalculator:
    """Helper class to encapsulate workflow cost calculation logic"""

    def __init__(self, runner_cost_config: "RunnerCostConfig"):
        self.runner_cost_config = runner_cost_config

    def _get_job_stats_base_query(
        self, workflow_id: int, start_date: datetime, end_date: datetime
    ):
        """Get the base job statistics query with common filters"""
        return JobStats.objects.filter(
            workflow_id=workflow_id,
            started_at__range=(start_date, end_date),
            labels__isnull=False,
        )

    def _annotate_costs(self, query):
        """Add cost calculation annotations to query"""
        return query.annotate(
            billable_minutes=ExpressionWrapper(
                (Extract(F("billable_time"), "epoch") / 60), output_field=DecimalField()
            ),
            max_rate=Coalesce(
                Subquery(
                    RunnerLabelMultiplier.objects.filter(
                        cost_config=self.runner_cost_config,
                        label=OuterRef("labels__label"),
                    ).values("per_minute_rate")[:1]
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(),
            ),
        ).annotate(
            job_cost=ExpressionWrapper(
                F("billable_minutes") * F("max_rate"), output_field=DecimalField()
            )
        )


class RunnerCostConfig(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="runner_cost_config"
    )

    class Meta:
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["user_id", "id"]),
        ]

    def calculate_workflow_costs(
        self, workflow_id: int, start_date: datetime, end_date: datetime
    ):
        """
        Calculate the total cost of workflow runs based on job labels and their associated rates.

        Args:
            workflow_id: ID of the workflow to calculate costs for
            start_date: Start date filter for job statistics
            end_date: End date filter for job statistics

        Returns:
            Decimal: Total cost of all jobs in the workflow during the specified period
        """
        calculator = WorkflowCostCalculator(self)

        # Get base query
        job_stats = (
            calculator._get_job_stats_base_query(workflow_id, start_date, end_date)
            .select_related("job")
            .prefetch_related("labels")
        )

        # Calculate total
        total_cost = calculator._annotate_costs(job_stats).aggregate(
            total_cost=Sum("job_cost", default=Decimal("0.00"))
        )["total_cost"]

        return total_cost or Decimal("0.00")

    def calculate_repository_costs(
        self, repository_id: int, start_date: datetime, end_date: datetime
    ) -> Decimal:
        """
        Calculate the total cost of a repository's workflow runs based on job labels and their associated rates.

        Args:
            repository_id: ID of the repository to calculate costs for
            start_date: Start date filter for job statistics
            end_date: End date filter for job statistics

        Returns:
            Decimal: Total cost of all jobs in the repository during the specified period
        """
        calculator = WorkflowCostCalculator(self)

        # Get base query for all jobs in the repository
        job_stats = JobStats.objects.filter(
            repository_id=repository_id,
            started_at__range=(start_date, end_date),
            labels__isnull=False,
        )

        # Calculate total
        total_cost = calculator._annotate_costs(job_stats).aggregate(
            total_cost=Sum("job_cost", default=Decimal("0.00"))
        )["total_cost"]

        return total_cost or Decimal("0.00")

    def calculate_repository_daily_costs(
        self,
        repository_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> QuerySet:
        """
        Calculate daily costs for all workflows in a repository.

        Args:
            repository_id: ID of the repository to calculate costs for
            start_date: Start date filter for job statistics
            end_date: End date filter for job statistics

        Returns:
            QuerySet: Daily cost aggregations with workflow details
        """
        calculator = WorkflowCostCalculator(self)

        # Get base query for all jobs in the repository
        job_stats = JobStats.objects.filter(
            repository_id=repository_id,
            started_at__range=(start_date, end_date),
            labels__isnull=False,
        )

        # Calculate daily totals grouped by workflow
        daily_costs = (
            calculator._annotate_costs(job_stats)
            .annotate(date=TruncDate("started_at"))
            .values("date", "workflow_id", "workflow__name")
            .annotate(
                daily_cost=Sum("job_cost", default=Decimal("0.00")),
                total_jobs=Count("id"),
                total_duration=Sum("execution_time"),
                total_billable_time=Sum("billable_time"),
            )
            .order_by("date", "workflow_id")
        )

        return daily_costs

    def calculate_repository_workflow_summary(
        self,
        repository_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """
        Calculate a summary of costs and usage for each workflow in a repository.

        Args:
            repository_id: ID of the repository to calculate costs for
            start_date: Start date filter for job statistics
            end_date: End date filter for job statistics

        Returns:
            QuerySet: Summary statistics for each workflow
        """
        calculator = WorkflowCostCalculator(self)

        # Get base query
        job_stats = JobStats.objects.filter(
            repository_id=repository_id,
            started_at__range=(start_date, end_date),
            labels__isnull=False,
        )

        # Calculate summary per workflow
        workflow_summary = (
            calculator._annotate_costs(job_stats)
            .values("workflow_id", "workflow__name")
            .annotate(
                total_cost=Sum("job_cost", default=Decimal("0.00")),
                total_runs=Count("workflow_run_id", distinct=True),
                avg_duration=Avg("execution_time"),
                avg_cost_per_run=ExpressionWrapper(
                    F("total_cost") / F("total_runs"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            )
            .order_by("-total_cost")
        )

        return [
            {
                "id": item["workflow_id"],
                "name": item["workflow__name"],
                "total_cost": item["total_cost"],
                "total_runs": item["total_runs"],
                "avg_duration": round_duration_to_seconds(item["avg_duration"]),
                "avg_cost_per_run": item["avg_cost_per_run"],
            }
            for item in workflow_summary
        ]

    def calculate_job_analysis_for_workflow(
        self, workflow_id: int, start_date: datetime, end_date: datetime
    ):
        # Get total number of workflow runs for percentage calculation
        total_runs = (
            JobStats.objects.filter(
                workflow_id=workflow_id, started_at__range=(start_date, end_date)
            )
            .values("workflow_run_id")
            .distinct()
            .count()
        )

        analysis_annotated = (
            (
                JobStats.objects.filter(
                    workflow_id=workflow_id,
                    started_at__range=(start_date, end_date),
                    labels__isnull=False,
                )
                .values("job__name", "labels__label")
                .annotate(
                    name=F("job__name"),
                    run_count=Count("workflow_run", distinct=True),
                    execution_rate=ExpressionWrapper(
                        F("run_count") * 100.0 / total_runs,
                        output_field=DecimalField(max_digits=5, decimal_places=2),
                    ),
                    avg_duration=Avg("execution_time"),
                    avg_billable_minutes=ExpressionWrapper(
                        Avg(Extract(F("billable_time"), "epoch") / 60),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    ),
                    per_minute_rate=Coalesce(
                        Max(
                            Case(
                                When(
                                    labels__label__isnull=False,
                                    then=Subquery(
                                        RunnerLabelMultiplier.objects.filter(
                                            cost_config=self,
                                            label=OuterRef("labels__label"),
                                        ).values("per_minute_rate")[:1]
                                    ),
                                )
                            )
                        ),
                        Value(Decimal("0.00")),
                        output_field=DecimalField(),
                    ),
                )
            )
            .annotate(
                cost_impact=ExpressionWrapper(
                    F("avg_billable_minutes") * F("per_minute_rate"),
                    output_field=DecimalField(max_digits=10, decimal_places=3),
                )
            )
            .order_by("-cost_impact", "-execution_rate")
        )

        return [
            {
                "name": item["name"],
                "execution_rate": item["execution_rate"],
                "avg_duration": round_duration_to_seconds(item["avg_duration"]),
                "cost_impact": item["cost_impact"],
            }
            for item in analysis_annotated
        ]

    def calculate_recent_runs_for_workflow(self, workflow_id: int):
        calculator = WorkflowCostCalculator(self)

        recent_runs = (
            WorkflowRun.objects.filter_for_user(self.user)
            .filter(
                workflow_id=workflow_id,
                status="completed",
            )
            .order_by("-created_at")[:10]
            .values("run_id", "event", "run_started_at", "html_url", "conclusion")
        )

        result = []
        for run in recent_runs:
            job_stats = JobStats.objects.filter(workflow_run__run_id=run["run_id"])

            costs = calculator._annotate_costs(job_stats)

            run_data = {
                "id": run["run_id"],
                "trigger_type": run["event"],
                "conclusion": run["conclusion"],
                "started_at": run["run_started_at"],
                "duration": job_stats.aggregate(total_duration=Sum("execution_time"))[
                    "total_duration"
                ],
                "cost": costs.aggregate(
                    total_cost=Sum("job_cost", default=Decimal("0.00"))
                )["total_cost"],
                "html_url": run["html_url"],
            }
            result.append(run_data)

        return result

    def calculate_daily_workflow_costs(
        self,
        workflow_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[datetime.date, Decimal]:
        """
        Calculate the daily costs of workflow runs based on job labels and their associated rates.

        Args:
            workflow_id: ID of the workflow to calculate costs for
            start_date: Start date filter for job statistics
            end_date: End date filter for job statistics

        Returns:
            Dict[datetime.date, Decimal]: Dictionary mapping dates to their total costs
        """
        calculator = WorkflowCostCalculator(self)

        # Get base query
        job_stats = calculator._get_job_stats_base_query(
            workflow_id, start_date, end_date
        )

        # Calculate daily totals
        daily_costs = (
            calculator._annotate_costs(job_stats)
            .annotate(date=TruncDate("started_at"))
            .values("date")
            .annotate(daily_cost=Sum("job_cost", default=Decimal("0.00")))
            .order_by("date")
        )

        return daily_costs


class RunnerLabelMultiplier(models.Model):
    cost_config = models.ForeignKey(
        RunnerCostConfig, on_delete=models.CASCADE, related_name="label_multipliers"
    )
    label = models.CharField(max_length=100)
    per_minute_rate = models.DecimalField(
        help_text="Cost per minute for this runner label",
        default=Decimal(0),
        decimal_places=4,
        max_digits=10,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cost_config", "label"],
                name="unique_label_multiplier_per_cost_config",
            )
        ]
        indexes = [
            models.Index(fields=["cost_config_id", "label"]),
            models.Index(fields=["cost_config_id", "label", "-per_minute_rate"]),
            models.Index(fields=["label", "-per_minute_rate"]),
            models.Index(fields=["label", "cost_config_id", "-per_minute_rate"]),
        ]

    def calculate_github_hosted_cost(self):
        rate = settings.GITHUB_HOSTED_RUNNER_COSTS.get(self.label.lower(), 0)
        if rate == 0:
            return
        return Decimal(rate)

    def save(self, *args, **kwargs):
        # If per_minute_rate is not set (0 or None), use calculated rate
        if not self.per_minute_rate:
            calculated_rate = self.calculate_github_hosted_cost()
            if calculated_rate is not None:
                self.per_minute_rate = calculated_rate
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_runner_cost_config(sender, instance, created, **kwargs):
    if created:
        RunnerCostConfig.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_runner_cost_config(sender, instance, **kwargs):
    instance.runner_cost_config.save()
