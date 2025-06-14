import subprocess, base64
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseForbidden,
    StreamingHttpResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import login

from gitsap.accounts.models import User
from gitsap.projects.models import Project
from gitsap.git.tasks import dispatch_gitsap_pipeline


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

        if not auth_user:
            return HttpResponse(
                "Authentication required",
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Git Access"'},
            )

        login(request, auth_user)

        # Get the service requested by the client (git-upload-pack for clone/fetch)
        service = request.GET.get("service")

        # Only git-upload-pack (fetch/clone) and git-receive-pack (push) are valid
        if not service or service not in ["git-upload-pack", "git-receive-pack"]:
            return HttpResponseNotFound("Service not found")

        # Is this a write operation?
        is_write = service == "git-receive-pack"

        project = get_object_or_404(
            Project,
            handle=kwargs["handle"],
            namespace=kwargs["namespace"],
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
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            handle=kwargs["handle"],
            namespace=kwargs["namespace"],
        )

        cmd = ["git-upload-pack", "--stateless-rpc", project._local_git_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        def stream():
            try:
                for chunk in request:
                    if chunk:
                        p.stdin.write(chunk)
                p.stdin.close()
                while True:
                    out = p.stdout.read(8192)
                    if not out:
                        break
                    yield out
            finally:
                p.stdout.close()

        return StreamingHttpResponse(
            stream(), content_type="application/x-git-upload-pack-result"
        )


@method_decorator(csrf_exempt, name="dispatch")
class GitReceivePackView(View):
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            handle=kwargs["handle"],
            namespace=kwargs["namespace"],
        )

        cmd = ["git-receive-pack", "--stateless-rpc", project._local_git_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        def stream():
            branches = []

            try:
                first_chunk = True
                for chunk in request:
                    if first_chunk:
                        first_chunk = False

                        # Parse only the initial pkt-lines
                        lines = chunk.split(b"\n")
                        for line in lines:
                            if b"refs/heads/" in line:
                                try:
                                    parts = line.strip().split()
                                    if len(parts) >= 3:
                                        ref = parts[2]
                                        # Handle capabilities suffix in first line
                                        if b"\x00" in ref:
                                            ref = ref.split(b"\x00")[0]
                                        if ref.startswith(b"refs/heads/"):
                                            branch = ref[len(b"refs/heads/") :].decode()
                                            branches.append(branch)
                                except Exception:
                                    continue

                    if chunk:
                        p.stdin.write(chunk)
                p.stdin.close()

                while True:
                    out = p.stdout.read(8192)
                    if not out:
                        break
                    yield out
            finally:
                p.stdout.close()

                try:
                    project.update_cloud_resource_artifact()

                    for branch in branches:
                        # Dispatch pipeline for each branch
                        dispatch_gitsap_pipeline.delay(project.id, branch)
                except Exception as e:
                    print(f"Warning: Failed to update archive after push: {e}")

        return StreamingHttpResponse(
            stream(), content_type="application/x-git-receive-pack-result"
        )
