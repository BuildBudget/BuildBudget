from datetime import timedelta, datetime

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from django.utils.timezone import make_aware
from django.views.generic import DetailView

from actions_data.models import (
    OwnerEntity,
    Repository,
    WorkflowRun,
    JobStats,
    RunnerCostConfig,
)
from actions_data.models.runner_cost_config import WorkflowCostCalculator


class BaseOrganizationView(DetailView):
    model = OwnerEntity
    template_name = "actions_data/organization.html"
    CACHE_TIMEOUT = 60 * 30  # 30 minutes cache timeout

    def get_cache_key_prefix(self, user_id: int, org_id: int) -> str:
        """Generate a cache key prefix for organization data"""
        return f"org_stats_{user_id}_{org_id}"

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

    def get_basic_stats(self, user: User, org: OwnerEntity, date_range: tuple) -> dict:
        """Get basic statistics with caching"""
        start_date, end_date = date_range
        cache_key = f"{self.get_cache_key_prefix(user.id, org.id)}_basic_stats_{start_date.date()}_{end_date.date()}"

        stats = cache.get(cache_key)
        if stats is not None:
            return stats

        workflow_runs = WorkflowRun.objects.filter(
            repository__users=user.userprofile.id,
            repository__owner=org,
            run_started_at__range=(start_date, end_date),
        )

        stats = {
            "total_runs": workflow_runs.count(),
            "total_workflows": workflow_runs.values("workflow_id").distinct().count(),
            "total_repositories": Repository.objects.filter(
                users=user.userprofile.id,
                owner=org,
            )
            .distinct()
            .count(),
        }

        cache.set(cache_key, stats, self.CACHE_TIMEOUT)
        return stats

    def get_trigger_analysis(
        self,
        user: User,
        org: OwnerEntity,
        date_range: tuple,
        calculator: WorkflowCostCalculator,
    ) -> list:
        """Get trigger analysis with caching"""
        start_date, end_date = date_range
        cache_key = f"{self.get_cache_key_prefix(user.id, org.id)}_trigger_analysis_{start_date.date()}_{end_date.date()}"

        analysis = cache.get(cache_key)
        if analysis is not None:
            return analysis

        job_stats = JobStats.objects.filter(
            repository__users=user.userprofile.id,
            repository__owner=org,
            started_at__range=(start_date, end_date),
        ).select_related("repository", "workflow")

        trigger_stats = (
            calculator._annotate_costs(job_stats)
            .values("event")
            .annotate(
                run_count=Count("workflow_run", distinct=True),
                total_cost=Sum("job_cost"),
                total_billable_minutes=Sum("billable_minutes"),
                avg_billable_minutes=Avg("billable_minutes"),
            )
            .order_by("-total_cost")
        )

        analysis = [
            {
                "trigger": stat["event"],
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

        cache.set(cache_key, analysis, self.CACHE_TIMEOUT)
        return analysis

    def get_repository_stats(
        self,
        user: User,
        org: OwnerEntity,
        date_range: tuple,
        calculator: WorkflowCostCalculator,
    ) -> list:
        """Get repository statistics with caching"""
        start_date, end_date = date_range
        cache_key = f"{self.get_cache_key_prefix(user.id, org.id)}_repository_stats_{start_date.date()}_{end_date.date()}"

        stats = cache.get(cache_key)
        if stats is not None:
            return stats

        job_stats = JobStats.objects.filter(
            repository__users=user.userprofile.id,
            repository__owner=org,
            started_at__range=(start_date, end_date),
        ).select_related("repository", "workflow")

        stats = (
            calculator._annotate_costs(job_stats)
            .values("repository_id", "repository__name")
            .annotate(
                run_count=Count("workflow_run", distinct=True),
                workflow_count=Count("workflow", distinct=True),
                total_cost=Sum("job_cost"),
                avg_execution_time=Avg("execution_time"),
            )
            .order_by("-total_cost")
        )

        cache.set(cache_key, list(stats), self.CACHE_TIMEOUT)
        return stats

    def get_daily_costs(
        self,
        user: User,
        org: OwnerEntity,
        date_range: tuple,
        calculator: WorkflowCostCalculator,
    ) -> dict:
        """Get daily costs with caching"""
        start_date, end_date = date_range
        cache_key = f"{self.get_cache_key_prefix(user.id, org.id)}_daily_costs_{start_date.date()}_{end_date.date()}"

        costs = cache.get(cache_key)
        if costs is not None:
            return costs

        job_stats = JobStats.objects.filter(
            repository__users=user.userprofile.id,
            repository__owner=org,
            started_at__range=(start_date, end_date),
        ).select_related("repository", "workflow")

        daily_costs_data = (
            calculator._annotate_costs(job_stats)
            .annotate(date=F("started_at__date"))
            .values("date", "repository__name")
            .annotate(daily_cost=Sum("job_cost"))
            .order_by("date")
        )

        # Organize daily costs by repository
        repos_data = {}
        for entry in daily_costs_data:
            date_str = entry["date"].strftime("%Y-%m-%d")
            if date_str not in repos_data:
                repos_data[date_str] = {}
            repos_data[date_str][entry["repository__name"]] = float(entry["daily_cost"])

        dates = sorted(repos_data.keys())

        repo_totals = {}
        for date_data in repos_data.values():
            for repo_name, cost in date_data.items():
                repo_totals[repo_name] = repo_totals.get(repo_name, 0) + cost

        repo_names = sorted(
            repo_totals.keys(), key=lambda x: repo_totals[x], reverse=True
        )

        costs = {
            "dates": dates,
            "repositories": [
                {
                    "name": repo_name,
                    "values": [
                        repos_data.get(date, {}).get(repo_name, 0) for date in dates
                    ],
                }
                for repo_name in repo_names
            ],
        }

        cache.set(cache_key, costs, self.CACHE_TIMEOUT)
        return costs

    def get_context_data(self, **kwargs):
        user = self.get_user()
        date_range = self.get_date_range()

        user_cost_config = RunnerCostConfig.objects.get(user_id=user.id)
        calculator = WorkflowCostCalculator(user_cost_config)

        context = super().get_context_data(**kwargs)
        context["start_date"], context["end_date"] = date_range

        # Get cached stats
        basic_stats = self.get_basic_stats(user, self.object, date_range)
        trigger_analysis = self.get_trigger_analysis(
            user, self.object, date_range, calculator
        )
        repository_stats = self.get_repository_stats(
            user, self.object, date_range, calculator
        )
        daily_costs = self.get_daily_costs(user, self.object, date_range, calculator)

        # Calculate total organization cost
        total_org_cost = sum(stat["total_cost"] or 0 for stat in repository_stats)

        context.update(
            {
                **basic_stats,
                "total_org_cost": total_org_cost,
                "avg_cost_per_run": (
                    total_org_cost / basic_stats["total_runs"]
                    if basic_stats["total_runs"] > 0
                    else 0
                ),
                "cost_trend": daily_costs,
                "trigger_analysis": trigger_analysis,
                "repository_stats": repository_stats,
            }
        )

        return context


class OrganizationView(LoginRequiredMixin, UserPassesTestMixin, BaseOrganizationView):
    def test_func(self):
        user = self.request.user
        org_id = self.request.resolver_match.kwargs.get("pk")
        return user.userprofile.repositories.filter(owner_id=org_id).exists()


class DemoOrganizationView(BaseOrganizationView):
    template_name = "actions_data/demo_organization.html"
    CACHE_TIMEOUT = settings.DEMO_CACHE_TIMEOUT  # Use longer cache timeout for demo

    def get_user(self):
        demo_username = settings.DEMO_USERNAME
        return User.objects.get(username=demo_username)
