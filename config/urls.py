from django.contrib import admin
from django.urls import path, include, re_path

from home.views import IndexView
from accounts.views import LoginView, RegisterView
from projects.views import (
    ProjectOverview,
    ProjectCreateView,
    GitInfoRefsView,
    GitUploadPackView,
    GitReceivePackView,
    ProjectTreeView,
)

project_browse_urlpatterns = [
    re_path(
        r"^tree/(?P<ref>[^/]+)(?P<relative_path>/.*)?$",
        ProjectTreeView.as_view(),
        name="project-tree",
    )
]

# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="accounts-login"),
    path("accounts/register/", RegisterView.as_view(), name="accounts-register"),
    path("create/", ProjectCreateView.as_view(), name="project-create"),
    
    path("<str:username>/<str:project_handle>/", ProjectOverview.as_view(), name="project-overview"),
    path("<str:username>/<str:project_handle>/-/", include(project_browse_urlpatterns)),

    # Git endpoints for handling git operations
    path("<str:username>/<str:project_handle>.git/info/refs", GitInfoRefsView.as_view(), name="project-git-info-refs"),
    path("<str:username>/<str:project_handle>.git/git-upload-pack", GitUploadPackView.as_view(), name="project-git-upload-pack"),
    path("<str:username>/<str:project_handle>.git/git-receive-pack", GitReceivePackView.as_view(), name="project-git-receive-pack"),

    path("", IndexView.as_view(), name="home-index"),
]
