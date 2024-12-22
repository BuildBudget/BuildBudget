from .webhook import WebhookView
from .landing_page import LandingPageView, AboutPageView
from .stats import (
    StatsByJobView,
    StatsByRepoView,
    StatsByOrgView,
    DemoStatsByJobView,
    DemoStatsByRepoView,
    DemoStatsByOrgView,
    StatsByWorkflowView,
    DemoStatsByWorkflowView,
    ImpersonatedStatsByWorkflowView,
)
from .registration import (
    SignUpView,
    CustomLogoutView,
)
from .new_webhook_status import NewWebhookStatusView
from .github_es_webhook_settings import GithubESWebhookSettingsView
from .github_com_webhook_settings import GithubComWebhookSettingsView
from .label_management import LabelManagementView, DemoLabelManagementView
from .workflow import WorkflowView, DemoWorkflowView
from .omnisearch import OmniSearchView, DemoOmnisearchView
from .repository import RepositoryView, DemoRepositoryView
from .organization import OrganizationView, DemoOrganizationView
