from django.urls import path, include
from rest_framework.routers import SimpleRouter

from gitsap.users.views import LoginView, RegisterView, LogoutView
from gitsap.home.views import IndexView

from gitsap.users.api import UserViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r"users", UserViewSet, basename="user")

# fmt: off
urlpatterns = [
    path("api/", include(router.urls)),
    path("users/login/", LoginView.as_view(), name="login"),
    path("users/register/", RegisterView.as_view(), name="register"),
    path("users/logout/", LogoutView.as_view(), name="logout"),
    path("", IndexView.as_view(), name="index"),
]
