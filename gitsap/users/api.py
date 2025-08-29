from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from gitsap.base.responses import success_response, error_response


class UserViewSet(ViewSet):
    @action(detail=False, methods=["get"])
    def profile(self, request, *args, **kwargs):
        data = {
            "is_authenticated": False,
            "new_user": True,
        }
        return success_response(data=data)