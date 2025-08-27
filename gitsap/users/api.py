from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from rest_framework.response import Response

class UserViewSet(ViewSet):
    @action(detail=False, methods=["get"])
    def profile(self, request, *args, **kwargs):
        return Response({"message": "User profile data", "is_authenticated": request.user.is_authenticated})