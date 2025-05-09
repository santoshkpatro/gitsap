import subprocess
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from projects.models import Project


class ProjectOverview(View):
    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project, handle=kwargs["project_handle"], owner__username=kwargs["username"]
        )
        context = {"project": project, "repo_objects": project.root_tree_objects}
        return render(request, "projects/overview.html", context)


@method_decorator(csrf_exempt, name="dispatch")
class GitInfoRefsView(View):
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
