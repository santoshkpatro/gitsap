from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import Http404

from gitsap.git.core import FILE_MAP
from gitsap.utils.template import vite_render
from gitsap.projects.mixin import ProjectPermissionMixin


class ProjectNewView(LoginRequiredMixin, View):
    def get(self, request):
        return vite_render(request, "pages/projects/new.js")


class ProjectOverviewView(ProjectPermissionMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        context = {
            "current_nodepath": None,
            "branches": project.git.list_branches(),
            "objects": project.git.list_tree(project.default_branch, None),
            "current_branch": project.default_branch,
        }
        return render(request, "projects/overview.html", context)


class ProjectBranchesView(ProjectPermissionMixin, LoginRequiredMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        current_path = kwargs.get("current_path", "/")
        project = request.project
        context = {
            "project": project,
            "branches": project.git.list_branches(),
            "current_path": current_path,
        }
        return render(request, "projects/branches.html", context)


class ProjectTreeResolveView(ProjectPermissionMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        context = {
            "current_nodepath": kwargs.get("nodepath", None),
            "branches": project.git.list_branches(),
            "objects": project.git.list_tree(
                kwargs.get("branch"), kwargs.get("nodepath", None)
            ),
            "current_branch": kwargs.get("branch"),
        }
        if request.htmx:
            return render(request, "projects/_tree.html", context)
        return render(request, "projects/tree.html", context)


class ProjectBlobResolveView(ProjectPermissionMixin, LoginRequiredMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        blob_content = project.git.get_blob_content(
            kwargs.get("branch"), kwargs.get("nodepath")
        )
        if blob_content is None:
            raise Http404("Blob not found")

        # detect file type for CodeMirror
        path = kwargs.get("nodepath")
        ext = "." + path.split(".")[-1] if "." in path else ""
        file_type = FILE_MAP.get(ext.lower(), "null")

        context = {
            "project": project,
            "current_branch": kwargs.get("branch"),
            "content": blob_content,
            "current_nodepath": kwargs.get("nodepath"),
            "file_type": file_type,
        }

        return render(request, "projects/blob.html", context)
