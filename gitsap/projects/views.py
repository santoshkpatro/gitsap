from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import Http404
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.views import APIView

from gitsap.users.models import User
from gitsap.projects.models import Project, ProjectPermission
from gitsap.git.core import FILE_MAP
from gitsap.utils.template import vite_render
from gitsap.projects.mixin import ProjectPermissionMixin
from gitsap.projects.serializers import ProjectVerifyAccessSerializer


class ProjectVerifyAccessAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ProjectVerifyAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            username=serializer.validated_data["username"]
        ).first()
        if not user or not user.check_password(serializer.validated_data["password"]):
            return Response(
                {"allowed": False, "reason": "Invalid credentials"}, status=403
            )
        project = Project.objects.filter(
            namespace=serializer.validated_data["namespace"]
        ).first()
        if not project:
            return Response(
                {"allowed": False, "reason": "Project not found"}, status=404
            )

        if project.visibility == "private":
            # Check for permissions
            if not ProjectPermission.objects.filter(
                project=project, user=user
            ).exists():
                return Response(
                    {"allowed": False, "reason": "Access denied"}, status=403
                )

        # TODO: Further check if service is allowed for this user/project
        return Response({"allowed": True, "reason": "Access granted"})


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
        branch = kwargs.get("branch")
        nodepath = kwargs.get("nodepath", None)
        current_nodepath = nodepath.strip("/") if nodepath else None
        backlink_url = ""

        if current_nodepath:
            parts = [p for p in current_nodepath.split("/") if p]
            parent = "/".join(parts[:-1])
            if parent:
                backlink_url = reverse(
                    "project-tree",
                    kwargs={
                        "namespace": project.namespace,
                        "branch": branch,
                        "nodepath": parent,
                    },
                )
            else:
                # Parent is root
                backlink_url = reverse(
                    "project-root-tree",
                    kwargs={
                        "namespace": project.namespace,
                        "branch": branch,
                    },
                )

        context = {
            "current_nodepath": current_nodepath,
            "branches": project.git.list_branches(),
            "objects": project.git.list_tree(
                kwargs.get("branch"), kwargs.get("nodepath", None)
            ),
            "current_branch": branch,
            "backlink_url": backlink_url,
            "node_last_commit": project.git.last_commit_for_node(branch, nodepath),
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
