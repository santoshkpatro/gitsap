from django.urls import path, include

from gitsap.users.views import (
    LoginView,
    LogoutView,
    RegisterView,
    UsernameCheckView,
    VerificationConfirmView,
    VerificationResendView,
)
from gitsap.home.views import IndexView
from gitsap.projects.views import ProjectNewView

# fmt: off
urlpatterns = [
    path("users/register/", RegisterView.as_view(), name="users-register"),
    path("users/login/", LoginView.as_view(), name="users-login"),
    path("users/logout/", LogoutView.as_view(), name="users-logout"),
    path("users/check-username/", UsernameCheckView.as_view(), name="users-check-username"),
    path("users/verify/<str:uidb64>/confirm/<str:token>/", VerificationConfirmView.as_view(), name="users-verification-confirm"),
    path("users/verify/<str:uidb64>/resend/", VerificationResendView.as_view(), name="users-verification-resend"),
    path("new/", ProjectNewView.as_view(), name="project-new"),
    path("", IndexView.as_view(), name="index"),
]
