from django.urls import path, include
from rest_framework.routers import SimpleRouter

from gitsap.users.views import LoginView
from gitsap.users.api import UserViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r"users", UserViewSet, basename="user")

# fmt: off
urlpatterns = [
    path("users/login/", LoginView.as_view(), name="login"),
    path("api/", include(router.urls)),
]
