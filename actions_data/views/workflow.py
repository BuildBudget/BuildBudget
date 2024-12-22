from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg, F
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.generic import DetailView

from actions_data.models import (
    Workflow,
    WorkflowRun,
    JobStats,
    RunnerCostConfig,
    Repository,
)
from utils import round_duration_to_seconds


class BaseWorkflowView(DetailView):
    model = Workflow
    template_name = "actions_data/workflow.html"

    def get_date_range(self):
        """Get date range from URL parameters or default to last 30 days"""
        today = timezone.now().date()
        default_start = today - timedelta(days=30)

        # Get dates from URL parameters
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            else:
                start_date = default_start

            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            else:
                end_date = today

            # Ensure end_date is not in the future
            if end_date > today:
                end_date = today

            # Ensure start_date is not after end_date
            if start_date > end_date:
                start_date = end_date - timedelta(days=6)

        except ValueError:
            # If there's any error parsing dates, use defaults
            start_date = default_start
            end_date = today

        # Convert to datetime with time at start/end of day
        start_datetime = make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = make_aware(datetime.combine(end_date, datetime.max.time()))

        return start_datetime, end_datetime

    def get_user(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        user = self.get_user()
        start_date, end_date = self.get_date_range()
        workflow_runs = WorkflowRun.objects.filter_for_user(user).filter(
            workflow=self.object,
            run_started_at__range=(start_date, end_date),
        )
        job_stats = (
            JobStats.objects.filter_for_user(user)
            .filter(
                workflow=self.object,
                started_at__range=(start_date, end_date),
            )
            .select_related("job")
        )
        context = super().get_context_data(**kwargs)
        # Add date range to context for form
        context["start_date"] = start_date
        context["end_date"] = end_date
        user_cost_config = RunnerCostConfig.objects.get(user_id=user.id)
        # Basic statistics
        # Count of distinct workflow runs
        total_runs = job_stats.aggregate(
            total_runs=Count("workflow_run", distinct=True)
        )["total_runs"]

        # Trigger analysis
        trigger_distribution = list(
            workflow_runs.values("event")
            .annotate(value=Count("id"))
            .values("value", name=F("event"))
        )

        # Time metrics

        avg_times = (
            job_stats.values("workflow_run")
            .annotate(
                total_execution_time=Sum("execution_time"),
                total_billable_time=Sum("billable_time"),
            )
            .aggregate(
                avg_execution_time=Avg("total_execution_time"),
                avg_billable_time=Avg("total_billable_time"),
            )
        )
        avg_execution_time = round_duration_to_seconds(avg_times["avg_execution_time"])
        avg_billable_time = round_duration_to_seconds(avg_times["avg_billable_time"])

        total_workflow_cost = user_cost_config.calculate_workflow_costs(
            workflow_id=self.object.id,
            start_date=start_date,
            end_date=end_date,
        )

        # Daily cost trend
        daily_costs_data = user_cost_config.calculate_daily_workflow_costs(
            workflow_id=self.object.id, start_date=start_date, end_date=end_date
        )
        daily_costs = {
            "dates": [c["date"].strftime("%Y-%m-%d") for c in daily_costs_data],
            "values": [float(c["daily_cost"]) for c in daily_costs_data],
        }
        jobs_analysis = user_cost_config.calculate_job_analysis_for_workflow(
            workflow_id=self.object.id, start_date=start_date, end_date=end_date
        )

        # Recent runs
        recent_runs = user_cost_config.calculate_recent_runs_for_workflow(
            workflow_id=self.object.id
        )

        context.update(
            {
                "total_runs": total_runs,
                "total_workflow_cost": total_workflow_cost,
                "avg_cost_per_run": (
                    total_workflow_cost / total_runs if total_runs > 0 else 0
                ),
                "cost_trend": daily_costs,
                "avg_execution_time": avg_execution_time,
                "avg_billable_time": avg_billable_time,
                "trigger_distribution": trigger_distribution,
                "jobs_analysis": jobs_analysis,
                "recent_runs": recent_runs,
            }
        )

        return context


class WorkflowView(LoginRequiredMixin, UserPassesTestMixin, BaseWorkflowView):

    def test_func(self):
        user = self.request.user
        workflow_id = self.request.resolver_match.kwargs.get("pk")
        try:
            repo_id = Workflow.objects.get(id=workflow_id).repository_id
        except Workflow.DoesNotExist:
            # So the view returns a 404
            return True
        return user.userprofile.repositories.filter(id=repo_id).exists()


class DemoWorkflowView(BaseWorkflowView):
    template_name = "actions_data/demo_workflow.html"

    def get_user(self):
        demo_username = settings.DEMO_USERNAME
        return User.objects.get(username=demo_username)
