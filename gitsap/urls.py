from django.contrib import admin
from django.urls import path

from gitsap.config.views import ConfigOnboardingView
from gitsap.projects.views import ProjectNewView, ProjectDetailView
from gitsap.root.views import RootHealthView, RootHomeView

# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("config/onboarding/<str:step>/", ConfigOnboardingView.as_view(), name="config-onboarding"),
    path("health/", RootHealthView.as_view(), name="root-health"),
    path("projects/new/", ProjectNewView.as_view(), name="project-new"),
    path("<slug:project_slug>/", ProjectDetailView.as_view(), name="project-detail"),
    path("", RootHomeView.as_view(), name="root-home")
]
