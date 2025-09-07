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


class ProjectRootTreeView(ProjectPermissionMixin, LoginRequiredMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        branch = kwargs.get("branch")

        context = {
            "project": project,
            "current_branch": branch or project.default_branch,
            "entries": project.git.list_tree(branch or project.default_branch),
            "current_path": "",
        }

        if request.htmx:
            return render(request, "projects/_entries.html", context)
        return render(request, "projects/tree.html", context)


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

        if request.htmx:
            return render(request, "projects/_entries.html", context)
        return render(request, "projects/tree.html", context)


class ProjectBlobView(ProjectPermissionMixin, LoginRequiredMixin, View):
    allowed_roles = ["read", "write", "admin", "owner", "triage", "maintain"]

    def get(self, request, *args, **kwargs):
        project = request.project
        branch = kwargs.get("branch")
        path = kwargs.get("path", None)

        blob_content = project.git.get_blob_content(
            branch or project.default_branch, path
        )
        if blob_content is None:
            raise Http404("Blob not found")

        # detect file type for CodeMirror
        ext = "." + path.split(".")[-1] if "." in path else ""
        file_type = FILE_MAP.get(ext.lower(), "null")

        context = {
            "project": project,
            "current_branch": branch or project.default_branch,
            "content": blob_content,
            "current_path": path,
            "file_type": file_type,
        }

        return render(request, "projects/blob.html", context)
