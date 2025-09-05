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
        context = {
            "project": request.project,
        }
        return render(request, "projects/overview.html", context)
