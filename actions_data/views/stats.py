from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.views.generic import TemplateView
from django.conf import settings

from actions_data.queries import get_chart_data
from actions_data.models.enums import (
    ChartType,
    AccumulatedMetricsResult,
    DateFilterOptions,
)
from actions_data.views.mixins.impersonation_mixin import ImpersonationMixin
from actions_data.views.services import (
    extract_date_filter,
    generate_chartjs_data,
    missing_labels,
)


class BaseStatsView(TemplateView):
    template_name: str = "actions_data/stats.html"
    chart_type: ChartType = None
    cache_timeout: int = settings.CACHES["default"]["TIMEOUT"]

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        return data

    def get_owner(self, request) -> User:
        return request.user

    def get_chart_data_with_cache(
        self,
        owner: User,
        date_filter: DateFilterOptions,
    ) -> list[AccumulatedMetricsResult]:
        cache_key = f"{owner.username}_{self.chart_type.value}_{date_filter}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        data = get_chart_data(
            owner=owner,
            date_filter=date_filter,
            chart_type=self.chart_type,
        )

        cache.set(cache_key, data, timeout=self.cache_timeout)
        return data

    def get_context_data(self, owner: User) -> dict[str, str]:
        date_filter = extract_date_filter(self.request)

        data = self.get_chart_data_with_cache(
            owner=owner,
            date_filter=date_filter,
        )

        adapted_data = self.adapt_data(data)

        return {
            "chart_data": generate_chartjs_data(adapted_data),
            "has_data": bool(data),
            "view": self.chart_type.value,
            "date_filter": date_filter.value,
            "missing_labels": missing_labels(owner),
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(self.get_owner(request))
        return self.render_to_response(context)


class StatsByJobView(LoginRequiredMixin, BaseStatsView):
    chart_type = ChartType.JOB

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("workflow_stats", args=[entry.entity_id])
        return data


class StatsByWorkflowView(LoginRequiredMixin, BaseStatsView):
    chart_type = ChartType.WORKFLOW

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("workflow_stats", args=[entry.entity_id])
        return data


class StatsByRepoView(LoginRequiredMixin, BaseStatsView):
    chart_type = ChartType.REPO

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("repository_stats", args=[entry.entity_id])
        return data


class StatsByOrgView(LoginRequiredMixin, BaseStatsView):
    chart_type = ChartType.ORG

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("organization_stats", args=[entry.entity_id])
        return data


class StatsByLabelsView(LoginRequiredMixin, BaseStatsView):
    chart_type = ChartType.LABELS


def _get_demo_user() -> User:
    demo_username = settings.DEMO_USERNAME
    return User.objects.get(username=demo_username)


class DemoBaseStatsView(BaseStatsView):
    template_name = "actions_data/demo_stats.html"
    chart_type = None
    cache_timeout = settings.DEMO_CACHE_TIMEOUT

    def get_owner(self, request) -> User:
        return _get_demo_user()


class DemoStatsByJobView(DemoBaseStatsView):
    chart_type = ChartType.JOB

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("demo_workflow_stats", args=[entry.entity_id])
        return data


class DemoStatsByWorkflowView(DemoBaseStatsView):
    chart_type = ChartType.WORKFLOW

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("demo_workflow_stats", args=[entry.entity_id])
        return data


class DemoStatsByRepoView(DemoBaseStatsView):
    chart_type = ChartType.REPO

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("demo_repository_stats", args=[entry.entity_id])
        return data


class DemoStatsByOrgView(DemoBaseStatsView):
    chart_type = ChartType.ORG

    def adapt_data(
        self,
        data: list[AccumulatedMetricsResult],
    ) -> list[AccumulatedMetricsResult]:
        for entry in data:
            entry.url = reverse("demo_organization_stats", args=[entry.entity_id])
        return data


class DemoStatsByLabelsView(DemoBaseStatsView):
    chart_type = ChartType.LABELS


class ImpersonatedStatsByWorkflowView(StatsByWorkflowView, ImpersonationMixin):
    pass
