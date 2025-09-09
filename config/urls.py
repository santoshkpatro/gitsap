from django.urls import path, re_path, include

from gitsap.users.views import (
    LoginView,
    LogoutView,
    RegisterView,
    UsernameCheckView,
    VerificationConfirmView,
    VerificationResendView,
)
from gitsap.home.views import IndexView
from gitsap.projects.views import (
    ProjectNewView,
    ProjectOverviewView,
    ProjectTreeResolveView,
    ProjectBlobResolveView,
    ProjectBranchesView,
    ProjectVerifyAccessAPIView,
)


# fmt: off
api_urlpatterns = [
    path("internal/projects/verify-access/", ProjectVerifyAccessAPIView.as_view(), name="api-project-verify-access"),
]

project_urlpattern = [
    path("tree/<str:branch>/", ProjectTreeResolveView.as_view(), name="project-root-tree"),
    path("tree/<str:branch>/<path:nodepath>/", ProjectTreeResolveView.as_view(), name="project-tree"),
    path("blob/<str:branch>/<path:nodepath>/", ProjectBlobResolveView.as_view(), name="project-blob"),
    # path("branches/", ProjectBranchesView.as_view(), name="project-branches"),
    path("", ProjectOverviewView.as_view(), name="project-overview"),
]

urlpatterns = [
    path("api/", include(api_urlpatterns)),
    path("users/register/", RegisterView.as_view(), name="users-register"),
    path("users/login/", LoginView.as_view(), name="users-login"),
    path("users/logout/", LogoutView.as_view(), name="users-logout"),
    path("users/check-username/", UsernameCheckView.as_view(), name="users-check-username"),
    path("users/verify/<str:uidb64>/confirm/<str:token>/", VerificationConfirmView.as_view(), name="users-verification-confirm"),
    path("users/verify/<str:uidb64>/resend/", VerificationResendView.as_view(), name="users-verification-resend"),
    path("new/", ProjectNewView.as_view(), name="project-new"),
    re_path(r'^(?P<namespace>[\w-]+/[\w-]+)/', include(project_urlpattern)),
    path("", IndexView.as_view(), name="index"),
]
