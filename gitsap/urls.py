from django.contrib import admin
from django.urls import path, include, re_path

from gitsap.home.views import IndexView
from gitsap.git.views import GitInfoRefsView, GitUploadPackView, GitReceivePackView
from gitsap.accounts.views import (
    LoginView,
    RegisterView,
    LogoutView,
    EmailVerificationConfirmView,
    EmailVerificationResendConfirmView,
)
from gitsap.projects.views import (
    ProjectOverview,
    ProjectCreateView,
    ProjectTreeView,
    ProjectBlobView,
    ProjectCommitHistoryView,
)
from gitsap.issues.views import (
    IssueListView,
    IssueCreateView,
    IssueDetailView,
    IssueCommentCreateView,
    IssueCloseView,
    IssueReOpenView,
)
from gitsap.pull_requests.views import (
    PullRequestCompareView,
    PullRequestListView,
    PullRequestCreateView,
    PullRequestDetailView,
    PullRequestMergeView,
    PullRequestConflictsView,
    PullRequestCommentCreateView,
)

# fmt: off
project_browse_urlpatterns = [
    re_path(r"^tree/(?P<ref_and_path>.+)$",  ProjectTreeView.as_view(), name="project-tree"),
    re_path(r"^blob/(?P<ref_and_path>.+)$",  ProjectBlobView.as_view(), name="project-blob"),
    re_path(r"^commits/(?P<ref>.+)$",  ProjectCommitHistoryView.as_view(), name="project-commit-history"),
]

# fmt: off
project_urlpatterns = [
    path("", ProjectOverview.as_view(), name="project-overview"),
    path("browse/", include(project_browse_urlpatterns)),
    path("issues/", IssueListView.as_view(), name="issue-list"),
    path("issues/create/", IssueCreateView.as_view(), name="issue-create"),
    path("issues/<int:issue_number>/", IssueDetailView.as_view(), name="issue-detail"),
    path("issues/<int:issue_number>/close/", IssueCloseView.as_view(), name="issue-close"),
    path("issues/<int:issue_number>/reopen/", IssueReOpenView.as_view(), name="issue-reopen"),
    path("issues/<int:issue_number>/comments/", IssueCommentCreateView.as_view(), name="issue-comment-create"),
    path("pull-requests/compare/", PullRequestCompareView.as_view(), name="pull-request-compare"),
    path("pull-requests/", PullRequestListView.as_view(), name="pull-request-list"),
    path("pull-requests/create/", PullRequestCreateView.as_view(), name="pull-request-create"),
    path("pull-requests/<int:pull_request_number>/", PullRequestDetailView.as_view(), name="pull-request-detail"),
    path("pull-requests/<int:pull_request_number>/merge/", PullRequestMergeView.as_view(), name="pull-request-merge"),
    path("pull-requests/<int:pull_request_number>/conflicts/", PullRequestConflictsView.as_view(), name="pull-request-conflicts"),
    path("pull-requests/<int:pull_request_number>/comments/", PullRequestCommentCreateView.as_view(), name="pull-request-comment-create"),
]


# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="accounts-login"),
    path("accounts/register/", RegisterView.as_view(), name="accounts-register"),
    path("accounts/logout/", LogoutView.as_view(), name="accounts-logout"),
    path("accounts/email-verification/re-send/", EmailVerificationResendConfirmView.as_view(), name="accounts-email-verification-resend"),
    path("accounts/email-verification/<str:uidb64>/<str:token>/", EmailVerificationConfirmView.as_view(), name="accounts-email-verification"),
    path("create/", ProjectCreateView.as_view(), name="project-create"),

    # Project endpoints
    path("<str:namespace>/<str:project_handle>/", include(project_urlpatterns)),

    # Git endpoints for handling git operations
    path("<str:namespace>/<str:project_handle>.git/info/refs", GitInfoRefsView.as_view(), name="project-git-info-refs"),
    path("<str:namespace>/<str:project_handle>.git/git-upload-pack", GitUploadPackView.as_view(), name="project-git-upload-pack"),
    path("<str:namespace>/<str:project_handle>.git/git-receive-pack", GitReceivePackView.as_view(), name="project-git-receive-pack"),
    path("", IndexView.as_view(), name="home-index"),
]
