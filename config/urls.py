from django.contrib import admin
from django.urls import path

from home.views import IndexView
from accounts.views import LoginView, RegisterView
from projects.views import ProjectOverview

# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="accounts-login"),
    path("accounts/register/", RegisterView.as_view(), name="accounts-register"),
    path("<str:username>/<str:project_handle>/", ProjectOverview.as_view(), name="project-overview"),
    path("", IndexView.as_view(), name="home-index"),
]
