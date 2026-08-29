from django.contrib import admin
from django.urls import path

from gitsap.config.views import ConfigOnboardingView
from gitsap.root.views import RootHealthView, RootHomeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("config/onboarding/<str:step>/", ConfigOnboardingView.as_view(), name="config-onboarding"),
    path("health/", RootHealthView.as_view(), name="root-health"),
    path("", RootHomeView.as_view(), name="root-home")
]
