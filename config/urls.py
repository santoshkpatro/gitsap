from django.contrib import admin
from django.urls import path

from home.views import IndexView
from accounts.views import LoginView, RegisterView
from projects.views import ProjectOverview, GitInfoRefsView, GitUploadPackView

# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="accounts-login"),
    path("accounts/register/", RegisterView.as_view(), name="accounts-register"),
    path("<str:username>/<str:project_handle>/", ProjectOverview.as_view(), name="project-overview"),

    # Git endpoints for handling git operations
    path("<str:username>/<str:project_handle>.git/info/refs", GitInfoRefsView.as_view(), name="project-git-info-refs"),
    path("<str:username>/<str:project_handle>.git/git-upload-pack", GitUploadPackView.as_view(), name="project-git-upload-pack"),
    path("", IndexView.as_view(), name="home-index"),
]
