from django.urls import path, include
from rest_framework.routers import SimpleRouter

from gitsap.users.views import LoginView
from gitsap.home.views import IndexView
from gitsap.projects.views import ProjectNewView

from gitsap.users.api import UserViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r"users", UserViewSet, basename="user")

# fmt: off
urlpatterns = [
    path("api/", include(router.urls)),
    path("users/login/", LoginView.as_view(), name="login"),
    path("new/", ProjectNewView.as_view(), name="project-new"),
    path("", IndexView.as_view(), name="index"),
]
