from django.shortcuts import render
from django.views import View
from django.db.models import Prefetch
from gitsap.pipelines.models import Pipeline, PipelineStep
from gitsap.projects.mixins import ProjectAccessMixin


class PipelineListView(ProjectAccessMixin, View):
    """
    View to list all pipelines for a given project.
    """

    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")
        project = request.project
        pipelines = (
            Pipeline.objects.filter(project=project)
            .order_by("-created_at")
            .select_related("triggered_by")
            .select_related("triggered_by__avatar")
            .prefetch_related(
                Prefetch(
                    "steps",
                    queryset=PipelineStep.objects.order_by("sequence").prefetch_related(
                        "jobs"
                    ),
                ),
            )
        )
        status = request.GET.get("status", "all")
        if status == "finished":
            pipelines = pipelines.filter(
                status__in=[
                    Pipeline.Status.SUCCESS,
                    Pipeline.Status.FAILED,
                    Pipeline.Status.CANCELLED,
                ]
            )

        context = {
            "project": project,
            "pipelines": pipelines,
            "active_tab": "pipelines",
            "status": status,
        }
        return render(request, "pipelines/pipeline_list.html", context)
