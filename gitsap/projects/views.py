from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from gitsap.utils.template import vite_render
from gitsap.projects.mixin import ProjectPermissionMixin


class ProjectNewView(LoginRequiredMixin, View):
    def get(self, request):
        return vite_render(request, "pages/projects/new.js")


class ProjectOverviewView(ProjectPermissionMixin, LoginRequiredMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        context = {
            "project": project,
            "branches": project.git.list_branches(),
            "entries": project.git.list_tree(project.default_branch),
            "current_branch": project.default_branch,
            "current_path": "",
        }
        return render(request, "projects/overview.html", context)


class ProjectTreeView(ProjectPermissionMixin, LoginRequiredMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        branch = kwargs.get("branch")
        path = kwargs.get("path", None)

        context = {
            "project": project,
            "current_branch": branch or project.default_branch,
            "entries": project.git.list_tree(branch or project.default_branch, path),
            "current_path": "{}/".format(path),
        }
        return render(request, "projects/tree.html", context)
