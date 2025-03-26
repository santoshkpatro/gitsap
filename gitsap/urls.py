from django.contrib import admin
from django.urls import path

from gitsap.users.views import LoginView
from gitsap.home.views import IndexView

# fmt: off
urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/login/", LoginView.as_view(), name="users-login"),
    path("", IndexView.as_view(), name="home-index"),
]
