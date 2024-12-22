from datetime import timedelta, datetime

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.generic import DetailView

from actions_data.models import Repository, WorkflowRun, JobStats, RunnerCostConfig
from actions_data.models.runner_cost_config import WorkflowCostCalculator


class BaseRepositoryView(DetailView):
    model = Repository
    template_name = "actions_data/repository.html"

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
            repository=self.object,
            run_started_at__range=(start_date, end_date),
        )

        user_cost_config = RunnerCostConfig.objects.get(user_id=user.id)
        calculator = WorkflowCostCalculator(user_cost_config)

        # Get base query for jobs including trigger info
        job_stats = JobStats.objects.filter(
            repository=self.object,
            started_at__range=(start_date, end_date),
            labels__isnull=False,
        ).select_related("workflow_run")

        context = super().get_context_data(**kwargs)
        context["start_date"] = start_date
        context["end_date"] = end_date

        # Basic statistics
        total_runs = workflow_runs.count()
        total_workflows = workflow_runs.values("workflow_id").distinct().count()

        # Enhanced trigger analysis with costs
        trigger_stats = (
            calculator._annotate_costs(job_stats)
            .values("workflow_run__event")
            .annotate(
                run_count=Count("workflow_run", distinct=True),
                total_cost=Sum("job_cost"),
                total_billable_minutes=Sum("billable_minutes"),
                avg_billable_minutes=Avg("billable_minutes"),
            )
            .order_by("-total_cost")
        )

        trigger_analysis = [
            {
                "trigger": stat["workflow_run__event"],
                "total_runs": stat["run_count"],
                "total_cost": stat["total_cost"] or 0,
                "avg_cost": (
                    (stat["total_cost"] or 0) / stat["run_count"]
                    if stat["run_count"] > 0
                    else 0
                ),
                "avg_billable_minutes": round(
                    float(stat["avg_billable_minutes"] or 0), 2
                ),
            }
            for stat in trigger_stats
        ]

        # Cost calculations
        total_repository_cost = user_cost_config.calculate_repository_costs(
            repository_id=self.object.id,
            start_date=start_date,
            end_date=end_date,
        )

        # Daily costs trend
        daily_costs_data = user_cost_config.calculate_repository_daily_costs(
            repository_id=self.object.id,
            start_date=start_date,
            end_date=end_date,
        )

        # Organize daily costs by workflow
        workflows_data = {}
        for entry in daily_costs_data:
            date_str = entry["date"].strftime("%Y-%m-%d")
            if date_str not in workflows_data:
                workflows_data[date_str] = {}
            workflows_data[date_str][entry["workflow__name"]] = float(
                entry["daily_cost"]
            )

        dates = sorted(workflows_data.keys())

        workflow_totals = {}
        for date_data in workflows_data.values():
            for workflow_name, cost in date_data.items():
                workflow_totals[workflow_name] = (
                    workflow_totals.get(workflow_name, 0) + cost
                )

        workflow_names = sorted(
            workflow_totals.keys(), key=lambda x: workflow_totals[x], reverse=True
        )

        daily_costs = {
            "dates": dates,
            "workflows": [
                {
                    "name": workflow_name,
                    "values": [
                        workflows_data.get(date, {}).get(workflow_name, 0)
                        for date in dates
                    ],
                }
                for workflow_name in workflow_names
            ],
        }

        # Workflow summary
        workflow_summary = user_cost_config.calculate_repository_workflow_summary(
            repository_id=self.object.id,
            start_date=start_date,
            end_date=end_date,
        )

        context.update(
            {
                "total_runs": total_runs,
                "total_workflows": total_workflows,
                "total_repository_cost": total_repository_cost,
                "avg_cost_per_run": (
                    total_repository_cost / total_runs if total_runs > 0 else 0
                ),
                "cost_trend": daily_costs,
                "trigger_analysis": trigger_analysis,
                "workflow_summary": workflow_summary,
            }
        )

        return context


class RepositoryView(LoginRequiredMixin, UserPassesTestMixin, BaseRepositoryView):
    def test_func(self):
        user = self.request.user
        repository_id = self.request.resolver_match.kwargs.get("pk")
        return user.userprofile.repositories.filter(id=repository_id).exists()


class DemoRepositoryView(BaseRepositoryView):
    template_name = "actions_data/demo_repository.html"

    def get_user(self):
        demo_username = settings.DEMO_USERNAME
        return User.objects.get(username=demo_username)
