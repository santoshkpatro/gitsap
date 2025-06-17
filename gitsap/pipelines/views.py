from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.views import View
from django.db.models import Prefetch
from gitsap.pipelines.models import Pipeline, PipelineStep, PipelineJob
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


class PipelineDetailView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")
        project = request.project
        pipeline = get_object_or_404(
            Pipeline, id=kwargs.get("pipeline_id"), project=project
        )
        current_tab = request.GET.get("tab", "workflow")
        context = {
            "project": project,
            "pipeline": pipeline,
            "current_tab": current_tab,
            "active_tab": "pipelines",
        }

        match current_tab:
            case "workflow":
                pipeline_steps = (
                    PipelineStep.objects.filter(pipeline=pipeline)
                    .order_by("sequence")
                    .prefetch_related("jobs")
                )
                context["pipeline_steps"] = pipeline_steps
            case "jobs":
                pipeline_jobs = (
                    PipelineJob.objects.filter(pipeline=pipeline)
                    .select_related("step")
                    .order_by("-created_at")
                )
                context["pipeline_jobs"] = pipeline_jobs
            case _:
                raise Http404("Tab not found")

        return render(request, f"pipelines/pipeline_detail.html", context)


class PipelineJobDetailView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")
        project = request.project
        pipeline_job = get_object_or_404(
            PipelineJob, id=kwargs.get("job_id"), pipeline__project=project
        )
        context = {
            "project": project,
            "pipeline_job": pipeline_job,
            "active_tab": "pipelines",
        }
        return render(request, "pipelines/pipeline_job_detail.html", context)
