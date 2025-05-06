from django.contrib import admin
from django.urls import path

from home.views import IndexView
from accounts.views import LoginView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(), name="accounts-login"),
    path("", IndexView.as_view(), name="home-index"),
]
