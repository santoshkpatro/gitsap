from django.views import View
from django.shortcuts import render

from gitsap.mixins import ProjectAccessMixin


class PipelineListView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pipelines"}
        return render(request, "pipelines/pipeline_list.html", context)


class PipelineDetailView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pipelines"}
        return render(request, "pipelines/pipeline_detail.html", context)


class PipelineCreateView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pipelines"}
        return render(request, "pipelines/pipeline_create.html", context)
