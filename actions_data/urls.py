from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import RedirectView

from actions_insider.settings import WEBHOOK_RELATIVE_URL
from .views import (
    LandingPageView,
    StatsByJobView,
    StatsByRepoView,
    StatsByOrgView,
    WebhookView,
    DemoStatsByJobView,
    DemoStatsByRepoView,
    DemoStatsByOrgView,
    CustomLogoutView,
    SignUpView,
    StatsByWorkflowView,
    DemoStatsByWorkflowView,
    NewWebhookStatusView,
    GithubComWebhookSettingsView,
    GithubESWebhookSettingsView,
    LabelManagementView,
    DemoLabelManagementView,
    AboutPageView,
    WorkflowView,
    DemoWorkflowView,
    ImpersonatedStatsByWorkflowView,
    OmniSearchView,
    DemoOmnisearchView,
    RepositoryView,
    DemoRepositoryView,
    OrganizationView,
    DemoOrganizationView,
)
from .views.stats import StatsByLabelsView, DemoStatsByLabelsView

urlpatterns = [
    path(WEBHOOK_RELATIVE_URL, WebhookView.as_view(), name="webhook"),
    path("", LandingPageView.as_view(), name="landing_page"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("stats/by-job/", StatsByJobView.as_view(), name="stats_by_job"),
    path("stats/by-workflow/", StatsByWorkflowView.as_view(), name="stats_by_workflow"),
    path(
        "impersonated/<int:user_id>/stats/by-workflow/",
        ImpersonatedStatsByWorkflowView.as_view(),
        name="impersonated_stats_by_workflow",
    ),
    path("stats/by-repo/", StatsByRepoView.as_view(), name="stats_by_repo"),
    path("stats/by-org/", StatsByOrgView.as_view(), name="stats_by_org"),
    path("stats/by-labels/", StatsByLabelsView.as_view(), name="stats_by_labels"),
    path("demo/", RedirectView.as_view(url="/demo/stats/by-workflow/")),
    path(
        "demo/stats/by-job/",
        DemoStatsByJobView.as_view(),
        name="demo_stats_by_job",
    ),
    path(
        "demo/stats/by-workflow/",
        DemoStatsByWorkflowView.as_view(),
        name="demo_stats_by_workflow",
    ),
    path(
        "demo/stats/by-repo/",
        DemoStatsByRepoView.as_view(),
        name="demo_stats_by_repo",
    ),
    path(
        "demo/stats/by-org/",
        DemoStatsByOrgView.as_view(),
        name="demo_stats_by_org",
    ),
    path(
        "demo/stats/by-labels/",
        DemoStatsByLabelsView.as_view(),
        name="demo_stats_by_labels",
    ),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path(
        "settings/webhooks/github-es/",
        GithubESWebhookSettingsView.as_view(),
        name="settings_webhooks_github_es",
    ),
    path(
        "settings/",
        GithubComWebhookSettingsView.as_view(),
        name="settings",
    ),
    path(
        "new-webhook-status/",
        NewWebhookStatusView.as_view(),
        name="new_webhook_status",
    ),
    path("settings/labels/", LabelManagementView.as_view(), name="label_management"),
    path(
        "demo/settings/labels/",
        DemoLabelManagementView.as_view(),
        name="demo_label_management",
    ),
    path("workflow/<int:pk>/", WorkflowView.as_view(), name="workflow_stats"),
    path(
        "demo/workflow/<int:pk>/",
        DemoWorkflowView.as_view(),
        name="demo_workflow_stats",
    ),
    path("api/search/", OmniSearchView.as_view(), name="api_search"),
    path("demo/api/search/", DemoOmnisearchView.as_view(), name="demo_api_search"),
    path(
        "repository/<int:pk>/",
        RepositoryView.as_view(),
        name="repository_stats",
    ),
    path(
        "demo/repository/<int:pk>/",
        DemoRepositoryView.as_view(),
        name="demo_repository_stats",
    ),
    path(
        "organization/<int:pk>/", OrganizationView.as_view(), name="organization_stats"
    ),
    path(
        "demo/organization/<int:pk>/",
        DemoOrganizationView.as_view(),
        name="demo_organization_stats",
    ),
]
