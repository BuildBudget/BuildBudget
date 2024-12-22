import json
from datetime import timedelta

from django.utils.timezone import now

from actions_data.models import JobStats, RunnerLabelMultiplier
from actions_data.models.enums import DateFilterOptions
from actions_data.queries import AccumulatedMetricsResult


def extract_date_filter(request) -> DateFilterOptions:
    date_filter = request.GET.get("date_filter")
    if date_filter:
        return DateFilterOptions(date_filter)
    return DateFilterOptions.PAST_WEEK


def generate_chartjs_data(data: list[AccumulatedMetricsResult]) -> str:
    # Sort data by execution time in descending order
    sorted_data = sorted(data, key=lambda x: x.sum_execution_time, reverse=True)

    # Prepare data for Chart.js
    chart_data = {
        "labels": [entry.name.split("/")[-1] for entry in sorted_data],
        "full_labels": [entry.name for entry in sorted_data],  # Full names for tooltips
        "urls": [entry.url for entry in sorted_data],
        "datasets": [
            {
                "label": "Execution time",
                "data": [
                    entry.sum_execution_time.total_seconds() for entry in sorted_data
                ],
                "backgroundColor": "rgba(58, 71, 80)",
                "borderColor": "rgba(58, 71, 80, 1.0)",
                "borderWidth": 1,
            },
            {
                "label": "Billable time",
                "data": [
                    entry.sum_billable_time.total_seconds() for entry in sorted_data
                ],
                "backgroundColor": "rgba(0, 123, 255, 0.6)",
                "borderColor": "rgba(58, 71, 80, 1.0)",
                "borderWidth": 1,
            },
            {
                "label": "Cost",
                "data": [float(entry.total_cost) for entry in sorted_data],
                "backgroundColor": "rgba(40, 167, 69, 0.6)",
                "borderColor": "rgba(58, 71, 80, 1.0)",
                "borderWidth": 1,
            },
        ],
    }

    return json.dumps(chart_data)


def missing_labels(user) -> list[str]:
    # Get all labels for the user
    all_labels = (
        JobStats.objects.filter_for_user(user)
        .filter(started_at__gt=now() - timedelta(days=30))
        .values_list("labels__label", flat=True)
    )
    # Get labels with non-zero per-minute-rate
    with_cost_values = RunnerLabelMultiplier.objects.filter(
        cost_config__user=user, label__in=all_labels, per_minute_rate__gt=0
    ).values_list("label", flat=True)

    all_labels_set = set(all_labels)
    if None in all_labels_set:
        all_labels_set.remove(None)
    with_cost_values_set = set(with_cost_values)
    if None in with_cost_values_set:
        with_cost_values_set.remove(None)
    return list(all_labels_set - with_cost_values_set)
