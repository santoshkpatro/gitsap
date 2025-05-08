from django.shortcuts import render, get_object_or_404
from django.views import View

from projects.models import Project


class ProjectOverview(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )
        context = {"project": project, "repo_objects": project.root_tree_objects}
        return render(request, "projects/overview.html", context)
