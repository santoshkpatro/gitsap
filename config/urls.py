from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse

from home.views import IndexView
from accounts.views import LoginView, RegisterView, LogoutView
from git.views import GitInfoRefsView, GitUploadPackView, GitReceivePackView
from projects.views import (
    ProjectOverview,
    ProjectCreateView,
    ProjectTreeView,
    ProjectBlobView,
    ProjectCommitHistoryView,
)
from issues.views import (
    IssueListView,
    IssueCreateView,
    IssueDetailView,
    IssueCommentCreateView,
    IssueCloseView,
    IssueReOpenView,
)
from pull_requests.views import (
    PullRequestCompareView,
    PullRequestListView,
    PullRequestCreateView,
)

project_browse_urlpatterns = [
    re_path(
        r"^tree/(?P<ref_and_path>.+)$",  # Capture entire string after /tree/
        ProjectTreeView.as_view(),
        name="project-tree",
    ),
    re_path(
        r"^blob/(?P<ref_and_path>.+)$",  # Capture entire string after /blob/
        ProjectBlobView.as_view(),
        name="project-blob",
    ),
    re_path(
        r"^commits/(?P<ref>.+)$",  # Capture entire string after /commits/
        ProjectCommitHistoryView.as_view(),
        name="project-commit-history",
    ),
]


# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="accounts-login"),
    path("accounts/register/", RegisterView.as_view(), name="accounts-register"),
    path("accounts/logout/", LogoutView.as_view(), name="accounts-logout"),
    path("create/", ProjectCreateView.as_view(), name="project-create"),
    
    path("<str:username>/<str:project_handle>/", ProjectOverview.as_view(), name="project-overview"),
    path("<str:username>/<str:project_handle>/browse/", include(project_browse_urlpatterns)),
    path("<str:username>/<str:project_handle>/issues/", IssueListView.as_view(), name="issue-list"),
    path("<str:username>/<str:project_handle>/issues/create/", IssueCreateView.as_view(), name="issue-create"),
    path("<str:username>/<str:project_handle>/issues/<int:issue_number>/", IssueDetailView.as_view(), name="issue-detail"),
    path("<str:username>/<str:project_handle>/issues/<int:issue_number>/close/", IssueCloseView.as_view(), name="issue-close"),
    path("<str:username>/<str:project_handle>/issues/<int:issue_number>/reopen/", IssueReOpenView.as_view(), name="issue-reopen"),
    path("<str:username>/<str:project_handle>/issues/<int:issue_number>/comments/", IssueCommentCreateView.as_view(), name="issue-comment-create"),
    path("<str:username>/<str:project_handle>/pull-requests/compare/", PullRequestCompareView.as_view(), name="pull-request-compare"),
    path("<str:username>/<str:project_handle>/pull-requests/", PullRequestListView.as_view(), name="pull-request-list"),
    path("<str:username>/<str:project_handle>/pull-requests/create/", PullRequestCreateView.as_view(), name="pull-request-create"),

    # Git endpoints for handling git operations
    path("<str:username>/<str:project_handle>.git/info/refs", GitInfoRefsView.as_view(), name="project-git-info-refs"),
    path("<str:username>/<str:project_handle>.git/git-upload-pack", GitUploadPackView.as_view(), name="project-git-upload-pack"),
    path("<str:username>/<str:project_handle>.git/git-receive-pack", GitReceivePackView.as_view(), name="project-git-receive-pack"),
    path("", IndexView.as_view(), name="home-index"),
]
