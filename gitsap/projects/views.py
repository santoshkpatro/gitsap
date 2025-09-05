from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from gitsap.utils.template import vite_render
from gitsap.projects.mixin import ProjectPermissionMixin
from gitsap.projects.models import ProjectPermission


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
        }
        return render(request, "projects/overview.html", context)
