from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection

from actions_data.models.enums import (
    DateFilterOptions,
    ChartType,
    AccumulatedMetricsResult,
)


def get_job_metrics_raw_sql(owner: User, start_date: datetime) -> list[dict]:
    """
    Get job metrics using optimized raw SQL query with CTEs.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH user_repositories AS (
                SELECT DISTINCT repository_id
                FROM actions_data_userprofile_repositories
                WHERE userprofile_id = %s
            ),
            runner_rates AS (
                SELECT DISTINCT ON (label)
                    label,
                    per_minute_rate
                FROM actions_data_runnerlabelmultiplier rm
                INNER JOIN actions_data_runnercostconfig rc ON rm.cost_config_id = rc.id
                WHERE rc.user_id = %s
                ORDER BY label, per_minute_rate DESC
            )
            SELECT
                js.owner_entity_name AS login,
                js.repository_name AS repo_name,
                js.workflow_name AS workflow_name,
                js.job_name AS job_name,
                js.workflow_id,
                SUM(js.execution_time) AS sum_execution_time,
                SUM(js.billable_time) AS sum_billable_time,
                SUM(
                    (EXTRACT(EPOCH FROM js.billable_time) / 60) *
                    COALESCE(rr.per_minute_rate, 0.00)
                ) AS total_cost,
                MAX(j.html_url) AS url
            FROM actions_data_jobstats js
            INNER JOIN user_repositories ur ON js.repository_id = ur.repository_id
            LEFT OUTER JOIN actions_data_jobstatslabel jsl ON js.id = jsl.job_stats_id
            LEFT OUTER JOIN runner_rates rr ON jsl.label = rr.label
            INNER JOIN actions_data_job j ON js.job_id = j.id
            WHERE js.started_at >= %s
            GROUP BY
                login,
                repo_name,
                workflow_name,
                job_name,
                js.workflow_id
            ORDER BY sum_execution_time DESC
            LIMIT 100;
        """,
            [owner.userprofile.id, owner.id, start_date],
        )

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def convert_raw_results_to_metrics(
    results: list[dict],
) -> list[AccumulatedMetricsResult]:
    """Convert raw SQL results into AccumulatedMetricsResult objects."""
    return [
        AccumulatedMetricsResult(
            entity_id=str(result["workflow_id"]),
            name=f"{result['login']}/{result['repo_name']} : {result['workflow_name']}/{result['job_name']}",
            sum_execution_time=result["sum_execution_time"],
            sum_billable_time=result["sum_billable_time"],
            total_cost=Decimal(str(result["total_cost"] or 0)),
            url=result["url"],
        )
        for result in results
    ]


def get_workflow_metrics_raw_sql(owner: User, start_date: datetime) -> list[dict]:
    """
    Get workflow metrics using optimized raw SQL query with CTEs.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH RECURSIVE
            user_repositories AS (
                SELECT DISTINCT repository_id
                FROM actions_data_userprofile_repositories
                WHERE userprofile_id = %s
            ),
            label_rates AS (
                SELECT DISTINCT ON (l.label)
                    l.label,
                    l.per_minute_rate
                FROM actions_data_runnerlabelmultiplier l
                JOIN actions_data_runnercostconfig c ON l.cost_config_id = c.id
                WHERE c.user_id = %s
                ORDER BY l.label, l.per_minute_rate DESC
            )
            SELECT
                js.owner_entity_name AS login,
                js.repository_name AS repo_name,
                js.workflow_name AS workflow_name,
                js.workflow_id,
                SUM(js.execution_time) AS sum_execution_time,
                SUM(js.billable_time) AS sum_billable_time,
                SUM(
                    (EXTRACT(EPOCH FROM js.billable_time) / 60) *
                    COALESCE(lr.per_minute_rate, 0.00)
                ) AS total_cost,
                MAX(w.html_url) AS url
            FROM actions_data_jobstats js
            INNER JOIN user_repositories ur
                ON js.repository_id = ur.repository_id
            LEFT OUTER JOIN actions_data_jobstatslabel jsl
                ON js.id = jsl.job_stats_id
            LEFT OUTER JOIN label_rates lr
                ON jsl.label = lr.label
            INNER JOIN actions_data_workflow w
                ON js.workflow_id = w.id
            WHERE js.started_at >= %s
            GROUP BY
                login,
                repo_name,
                workflow_name,
                js.workflow_id
            ORDER BY sum_execution_time DESC
            LIMIT 100;
            """,
            [owner.userprofile.id, owner.id, start_date],
        )

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def convert_workflow_results_to_metrics(
    results: list[dict],
) -> list[AccumulatedMetricsResult]:
    """Convert raw SQL results into AccumulatedMetricsResult objects for workflows."""
    return [
        AccumulatedMetricsResult(
            entity_id=str(result["workflow_id"]),
            name=f"{result['login']}/{result['repo_name']} : {result['workflow_name']}",
            sum_execution_time=result["sum_execution_time"],
            sum_billable_time=result["sum_billable_time"],
            total_cost=Decimal(str(result["total_cost"] or 0)),
            url=result["url"],
        )
        for result in results
    ]


def get_repo_metrics_raw_sql(owner: User, start_date: datetime) -> list[dict]:
    """
    Get repository metrics using optimized raw SQL query with CTEs.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH rate_lookup AS (
                SELECT DISTINCT ON (ajl.job_stats_id)
                    ajl.job_stats_id,
                    COALESCE(rlm.per_minute_rate, 0.00) as per_minute_rate
                FROM actions_data_jobstatslabel ajl
                LEFT JOIN actions_data_runnerlabelmultiplier rlm ON rlm.label = ajl.label
                LEFT JOIN actions_data_runnercostconfig rc ON rc.id = rlm.cost_config_id
                WHERE rc.user_id = %s
                ORDER BY ajl.job_stats_id, rlm.per_minute_rate DESC
            )
            SELECT
                js.owner_entity_name AS login,
                js.repository_name AS repo_name,
                js.repository_id,
                SUM(js.execution_time) AS sum_execution_time,
                SUM(js.billable_time) AS sum_billable_time,
                SUM((EXTRACT(EPOCH FROM js.billable_time) / 60) * rate_lookup.per_minute_rate) AS total_cost
            FROM actions_data_jobstats js
            LEFT JOIN actions_data_jobstatslabel ajl ON js.id = ajl.job_stats_id
            LEFT JOIN rate_lookup ON rate_lookup.job_stats_id = js.id
            WHERE js.repository_id IN (
                SELECT repository_id
                FROM actions_data_userprofile_repositories
                WHERE userprofile_id = %s
            )
            AND js.started_at >= %s
            GROUP BY login, repo_name, js.repository_id
            ORDER BY sum_execution_time DESC
            LIMIT 100;
            """,
            [owner.id, owner.userprofile.id, start_date],
        )

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def convert_repo_results_to_metrics(
    results: list[dict],
) -> list[AccumulatedMetricsResult]:
    """Convert raw SQL results into AccumulatedMetricsResult objects for repositories."""
    return [
        AccumulatedMetricsResult(
            entity_id=str(result["repository_id"]),
            name=f"{result['login']}/{result['repo_name']}",
            sum_execution_time=result["sum_execution_time"],
            sum_billable_time=result["sum_billable_time"],
            total_cost=Decimal(str(result["total_cost"] or 0)),
            url=f"https://github.com/{result['login']}/{result['repo_name']}",
        )
        for result in results
    ]


def get_label_metrics_raw_sql(owner: User, start_date: datetime) -> list[dict]:
    """
    Get label metrics using optimized raw SQL query with CTEs.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH repository_ids AS (
                SELECT DISTINCT u0.id
                FROM actions_data_repository u0
                INNER JOIN actions_data_userprofile_repositories u1
                    ON u0.id = u1.repository_id
                WHERE u1.userprofile_id = %s
            ),
            label_rates AS (
                SELECT
                    rlm.label,
                    MAX(rlm.per_minute_rate) as per_minute_rate
                FROM actions_data_runnerlabelmultiplier rlm
                INNER JOIN actions_data_runnercostconfig rcc
                    ON rlm.cost_config_id = rcc.id
                WHERE rcc.user_id = %s
                GROUP BY rlm.label
            )
            SELECT
                jsl.label,
                SUM(js.execution_time) AS sum_execution_time,
                SUM(js.billable_time) AS sum_billable_time,
                SUM(
                    (EXTRACT(EPOCH FROM js.billable_time) / 60) *
                    COALESCE(lr.per_minute_rate, 0.00)
                ) AS total_cost
            FROM actions_data_jobstats js
            LEFT OUTER JOIN actions_data_jobstatslabel jsl
                ON js.id = jsl.job_stats_id
            LEFT JOIN label_rates lr
                ON lr.label = jsl.label
            WHERE
                js.repository_id IN (SELECT id FROM repository_ids)
                AND js.started_at >= %s
                AND jsl.label IS NOT NULL
            GROUP BY jsl.label
            ORDER BY sum_execution_time DESC
            LIMIT 100;
            """,
            [owner.userprofile.id, owner.id, start_date],
        )

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def convert_label_results_to_metrics(
    results: list[dict],
) -> list[AccumulatedMetricsResult]:
    """Convert raw SQL results into AccumulatedMetricsResult objects for labels."""
    return [
        AccumulatedMetricsResult(
            entity_id=None,  # Labels don't have specific IDs
            name=result["label"],
            sum_execution_time=result["sum_execution_time"],
            sum_billable_time=result["sum_billable_time"],
            total_cost=Decimal(str(result["total_cost"] or 0)),
            url=None,  # Labels don't have URLs
        )
        for result in results
    ]


def get_org_metrics_raw_sql(owner: User, start_date: datetime) -> list[dict]:
    """
    Get organization metrics using optimized raw SQL query with CTEs.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH user_repositories AS (
                SELECT DISTINCT r.id
                FROM actions_data_repository r
                INNER JOIN actions_data_userprofile_repositories upr ON r.id = upr.repository_id
                WHERE upr.userprofile_id = %s
            ),
            runner_costs AS (
                SELECT
                    rlm.label,
                    MAX(rlm.per_minute_rate) as per_minute_rate
                FROM actions_data_runnerlabelmultiplier rlm
                INNER JOIN actions_data_runnercostconfig rcc ON rlm.cost_config_id = rcc.id
                WHERE rcc.user_id = %s
                GROUP BY rlm.label
            ),
            job_stats_aggregated AS (
                SELECT
                    js.owner_entity_name AS login,
                    js.owner_entity_id,
                    SUM(js.execution_time) as sum_execution_time,
                    SUM(js.billable_time) as sum_billable_time,
                    SUM(
                        EXTRACT(EPOCH FROM js.billable_time) / 60 *
                        COALESCE(rc.per_minute_rate, 0.00)
                    ) as total_cost
                FROM actions_data_jobstats js
                INNER JOIN user_repositories ur ON js.repository_id = ur.id
                LEFT JOIN actions_data_jobstatslabel jsl ON js.id = jsl.job_stats_id
                LEFT JOIN runner_costs rc ON jsl.label = rc.label
                WHERE js.started_at >= %s
                GROUP BY login, js.owner_entity_id
            )
            SELECT
                login,
                owner_entity_id,
                sum_execution_time,
                sum_billable_time,
                total_cost
            FROM job_stats_aggregated
            ORDER BY sum_execution_time DESC
            LIMIT 100;
            """,
            [owner.userprofile.id, owner.id, start_date],
        )

        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def convert_org_results_to_metrics(
    results: list[dict],
) -> list[AccumulatedMetricsResult]:
    """Convert raw SQL results into AccumulatedMetricsResult objects for organizations."""
    return [
        AccumulatedMetricsResult(
            entity_id=str(result["owner_entity_id"]),
            name=result["login"],
            sum_execution_time=result["sum_execution_time"],
            sum_billable_time=result["sum_billable_time"],
            total_cost=Decimal(str(result["total_cost"] or 0)),
            url=f"https://github.com/{result['login']}",
        )
        for result in results
    ]


def get_chart_data(
    owner: User,
    date_filter: DateFilterOptions,
    chart_type: ChartType,
) -> list[AccumulatedMetricsResult]:
    """Get chart data using optimized metrics aggregation"""

    chart_type_handlers = {
        ChartType.JOB: (get_job_metrics_raw_sql, convert_raw_results_to_metrics),
        ChartType.WORKFLOW: (
            get_workflow_metrics_raw_sql,
            convert_workflow_results_to_metrics,
        ),
        ChartType.REPO: (get_repo_metrics_raw_sql, convert_repo_results_to_metrics),
        ChartType.LABELS: (get_label_metrics_raw_sql, convert_label_results_to_metrics),
        ChartType.ORG: (get_org_metrics_raw_sql, convert_org_results_to_metrics),
    }

    get_metrics_func, convert_func = chart_type_handlers[chart_type]

    raw_results = get_metrics_func(
        owner=owner,
        start_date=date_filter.start_date,
    )
    return convert_func(raw_results)
