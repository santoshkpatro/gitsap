from django.urls import path
from gitsap.pipelines.consumers import JobRelayConsumer

urlpatterns = [
    path(
        "ws/pipelines/job/<uuid:job_id>/",
        JobRelayConsumer.as_asgi(),
        name="job-relay",
    ),
]
