from django.contrib import admin
from django.urls import path, re_path, include

from gitsap.views.projects import (
    RepoView,
    CommitsView,
    BranchesView,
    SettingsGeneralView,
    SettingsCollaboratorsView,
    SettingsBranchesView,
    SettingsRulesView,
    SettingsEnvironmentsView,
    SettingsWebhooksView,
)
from gitsap.views.issues import IssueListView, IssueDetailView, IssueCreateView
from gitsap.views.pull_requests import (
    PullRequestListView,
    PullRequestDetailView,
    PullRequestCreateView,
    PullRequestConfirmView,
)
from gitsap.views.pipelines import PipelineListView, PipelineDetailView, PipelineCreateView

project_urlpatterns = [
    # Code
    path("", RepoView.as_view(), name="repo"),
    path("commits/", CommitsView.as_view(), name="commits"),
    path("branches/", BranchesView.as_view(), name="branches"),

    # Issues
    path("issues/", IssueListView.as_view(), name="issue_list"),
    path("issues/new/", IssueCreateView.as_view(), name="issue_create"),
    path("issues/<str:issue_id>/", IssueDetailView.as_view(), name="issue_detail"),

    # Pull requests
    path("pull-requests/", PullRequestListView.as_view(), name="pull_request_list"),
    path("pull-requests/new/", PullRequestCreateView.as_view(), name="pull_request_create"),
    path("pull-requests/<str:pr_id>/", PullRequestDetailView.as_view(), name="pull_request_detail"),
    path("pull-requests/<str:pr_id>/confirm/", PullRequestConfirmView.as_view(), name="pull_request_confirm"),

    # Pipelines
    path("pipelines/", PipelineListView.as_view(), name="pipeline_list"),
    path("pipelines/new/", PipelineCreateView.as_view(), name="pipeline_create"),
    path("pipelines/<str:pipeline_id>/", PipelineDetailView.as_view(), name="pipeline_detail"),

    # Settings
    path("settings/", SettingsGeneralView.as_view(), name="settings_general"),
    path("settings/collaborators/", SettingsCollaboratorsView.as_view(), name="settings_collaborators"),
    path("settings/branches/", SettingsBranchesView.as_view(), name="settings_branches"),
    path("settings/rules/", SettingsRulesView.as_view(), name="settings_rules"),
    path("settings/environments/", SettingsEnvironmentsView.as_view(), name="settings_environments"),
    path("settings/webhooks/", SettingsWebhooksView.as_view(), name="settings_webhooks"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^(?P<namespace>[^/]+/[^/]+)/", include(project_urlpatterns)),
]
