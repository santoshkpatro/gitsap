import subprocess, base64
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.text import slugify
from django.urls import reverse
from datetime import datetime

from accounts.models import User
from projects.models import Project
from projects.forms import ProjectCreateForm


class ProjectCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = {
            "form": ProjectCreateForm(),
        }
        return render(request, "projects/create.html", context)

    def post(self, request, *args, **kwargs):
        form = ProjectCreateForm(request.POST)
        context = {"form": form}
        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return render(request, "projects/create.html", context)

        cleaned_data = form.cleaned_data
        existing_project = Project.objects.filter(
            owner=request.user, handle=slugify(cleaned_data["name"])
        )
        if existing_project.exists():
            form.add_error("name", "You already have a project with this name.")
            return render(request, "projects/create.html", context)

        project = Project(
            **cleaned_data,
        )
        project.owner = request.user
        project.save()

        return redirect(
            "project-overview",
            username=request.user.username,
            project_handle=project.handle,
        )


class ProjectOverview(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )
        current_ref = project.default_branch
        tree_browsable_path = reverse(
            "project-tree", args=[project.owner.username, project.handle, current_ref]
        )
        blob_browsable_path = reverse(
            "project-blob",
            args=[project.owner.username, project.handle, current_ref],
        )

        context = {
            "project": project,
            "repo_objects": project.root_tree_objects,
            "current_ref": current_ref,
            "tree_browsable_path": tree_browsable_path,
            "blob_browsable_path": blob_browsable_path,
            "last_commit": project.get_last_commit_info_for_ref(project.default_branch),
            "active_tab": "code",
        }
        return render(request, "projects/overview.html", context)


class GitOpsAuthenticationMixin:
    def has_project_git_action_permissions(self, project, user, is_write):
        is_public_project = project.visibility == Project.Visibility.PUBLIC

        if not is_write and is_public_project:
            return True

        return project.project_collaborators.filter(user=user).exists()


@method_decorator(csrf_exempt, name="dispatch")
class GitInfoRefsView(GitOpsAuthenticationMixin, View):
    def validate_auth_credentials(self, request):
        pass
        # Check if authentication header is present
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Basic "):
            return None

        # Decode the credentials
        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, password = auth_decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return None

        user = User.objects.filter(username=username).first()
        if not user:
            return None

        if not user.is_active:
            return None

        if not user.check_password(password):
            return None

        return user

    """
    Handle Git info/refs requests, which are used by clients to discover
    the capabilities of the server and initiate git clone/fetch operations.
    """

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to the info/refs endpoint.

        This endpoint is called by git clients to initiate a git operation.

        Args:
            request: The HTTP request
            repo_name: Repository name

        Returns:
            HttpResponse: Git protocol data
        """
        auth_user = self.validate_auth_credentials(request)

        if not auth_user and not self.request.user.is_authenticated:
            return HttpResponse(
                "Authentication required",
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Git Access"'},
            )

        if not auth_user:
            return HttpResponseForbidden("Invalid credentials")

        login(request, auth_user)

        # Get the service requested by the client (git-upload-pack for clone/fetch)
        service = request.GET.get("service")

        # Only git-upload-pack (fetch/clone) and git-receive-pack (push) are valid
        if not service or service not in ["git-upload-pack", "git-receive-pack"]:
            return HttpResponseNotFound("Service not found")

        # Is this a write operation?
        is_write = service == "git-receive-pack"

        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )

        # Check if the user has permission to perform the requested action
        if not self.has_project_git_action_permissions(project, auth_user, is_write):
            return HttpResponseForbidden("Permission denied")

        # Execute git command to get refs
        cmd = [service, "--stateless-rpc", "--advertise-refs", project._local_git_path]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        # Format the response according to Git Smart HTTP protocol
        packet = f"# service={service}\n"
        length = len(packet) + 4
        prefix = f"{length:04x}"

        # Git protocol format: [4-byte length][payload][0000]
        data = prefix.encode() + packet.encode() + b"0000" + p.stdout.read()

        # Set the appropriate content type for the response
        response = HttpResponse(data)
        response["Content-Type"] = f"application/x-{service}-advertisement"
        response["Cache-Control"] = "no-cache"

        return response


@method_decorator(csrf_exempt, name="dispatch")
class GitUploadPackView(View):
    """
    Handle Git upload-pack requests, which are used to transfer objects
    from the server to the client during git clone/fetch operations.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for git-upload-pack.

        This endpoint is called by git clients to download objects during
        clone/fetch operations.

        Args:
            request: The HTTP request
            repo_name: Repository name

        Returns:
            HttpResponse: Git protocol data with packed objects
        """
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )

        # Execute git command to handle the upload-pack request
        cmd = ["git-upload-pack", "--stateless-rpc", project._local_git_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # Pass the client's request body to git command
        stdout_data = p.communicate(input=request.body)[0]

        # Return the git command output
        response = HttpResponse(stdout_data)
        response["Content-Type"] = "application/x-git-upload-pack-result"

        return response


@method_decorator(csrf_exempt, name="dispatch")
class GitReceivePackView(View):
    """
    Handle Git receive-pack requests, which are used to transfer objects
    from the client to the server during git push operations.
    """

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )

        # Step 1: Handle the receive-pack request
        cmd = ["git-receive-pack", "--stateless-rpc", project._local_git_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout_data = p.communicate(input=request.body)[0]

        latest_commit_info = None

        try:
            # Step 2: Extract latest commit info
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%ct|%s"],
                cwd=project._local_git_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            if result.stdout.strip():
                commit_hash, timestamp, message = result.stdout.strip().split("|", 2)
                latest_commit_info = {
                    "hash": commit_hash,
                    "timestamp": datetime.fromtimestamp(int(timestamp)),
                    "message": message.strip(),
                }
        except subprocess.CalledProcessError as e:
            print("Failed to fetch commit:", e)

        # Step 3: Re-archive and upload to S3
        try:
            project.update_cloud_resource_artifact()
        except Exception as e:
            print(f"Warning: Failed to update archive after push: {e}")

        # Optionally log or return commit info for debugging
        print("Latest commit pushed:", latest_commit_info)

        response = HttpResponse(stdout_data)
        response["Content-Type"] = "application/x-git-receive-pack-result"
        return response


class ProjectTreeView(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )

        current_ref = kwargs.get("ref")
        relative_path = kwargs.get("relative_path", "/")
        repo_objects = project.get_tree_objects_at_path(
            ref_name=kwargs["ref"],
            relative_path=relative_path.strip("/"),
        )
        tree_browsable_path = reverse(
            "project-tree",
            args=[project.owner.username, project.handle, current_ref, relative_path],
        )
        blob_browsable_path = reverse(
            "project-blob",
            args=[project.owner.username, project.handle, current_ref, relative_path],
        )

        context = {
            "project": project,
            "repo_objects": repo_objects,
            "tree_browsable_path": tree_browsable_path,
            "blob_browsable_path": blob_browsable_path,
            "last_commit": project.get_last_commit_info(
                relative_path.strip("/"), current_ref
            ),
            "active_tab": "code",
        }
        return render(request, "projects/tree.html", context)


class ProjectBlobView(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )

        current_ref = kwargs["ref"]
        relative_path = kwargs["relative_path"].strip("/")
        repo_object = project.get_blob_at_path(
            ref_name=kwargs["ref"],
            relative_path=relative_path,
        )

        context = {
            "project": project,
            "repo_object": repo_object,
            "current_ref": current_ref,
            "last_commit": project.get_last_commit_info(relative_path, current_ref),
            "active_tab": "code",
        }
        return render(request, "projects/blob.html", context)
