from django.contrib import admin
from django.urls import path

from gitsap.users.views import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/login/", LoginView.as_view(), name="login"),
]
