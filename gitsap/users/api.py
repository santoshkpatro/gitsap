from django.contrib.auth import login as user_login
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from gitsap.base.responses import success_response, error_response
from gitsap.users.serializers import LoginSerializer, LoggedInUserSerializer
from gitsap.users.models import User


class UserViewSet(ViewSet):
    @action(detail=False, methods=["get"])
    def profile(self, request, *args, **kwargs):
        data = {
            "is_authenticated": False,
            "new_user": True,
        }
        return success_response(data=data)

    @action(detail=False, methods=["post"])
    def login(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(message="Invalid data", errors=serializer.errors)

        data = serializer.validated_data
        if "username" in data:
            query = {"username": data["username"]}
        elif "email" in data:
            query = {"email": data["email"]}
        else:
            return error_response(
                message="Username or email is required", error_code=422, status_code=422
            )
        user = User.objects.filter(**query).first()
        if not user:
            return error_response(
                message="No account found", error_code=404, status_code=404
            )

        if not user.check_password(data["password"]):
            return error_response(
                message="Please enter correct password", error_code=401, status_code=401
            )

        user_login(request, user)
        logged_user_serializer = LoggedInUserSerializer(user)
        data = {
            "logged_in_user": logged_user_serializer.data,
        }
        return success_response(data=data, message="Login successful")
