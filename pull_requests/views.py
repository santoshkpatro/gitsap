from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q

from projects.mixins import ProjectAccessMixin
from pull_requests.forms import PullRequestCreateForm
from pull_requests.models import PullRequest


class PullRequestListView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        status = request.GET.get("status", "open")
        if status == "all":
            status_filter = Q(status__in=["open", "closed"])
        else:
            status_filter = Q(status=status)

        pull_requests = (
            PullRequest.objects.filter(project=project)
            .filter(status_filter)
            .order_by("-pull_request_number")
        )
        context = {
            "project": project,
            "status": status,
            "pull_requests": pull_requests,
            "active_tab": "pull_requests",
        }
        return render(request, "pull_requests/list.html", context)


class PullRequestCompareView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        source_branch = request.GET.get("source", project.default_branch)
        target_branch = request.GET.get("target", project.default_branch)

        diffs = project.get_diff_between_branches(source_branch, target_branch)
        commits = project.get_commit_diff_between_refs(source_branch, target_branch)
        total_additions = sum(f["added_lines"] for f in diffs)
        total_deletions = sum(f["deleted_lines"] for f in diffs)

        context = {
            "project": project,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "diffs": diffs,
            "commits": commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "active_tab": "pull_requests",
        }
        return render(request, "pull_requests/compare.html", context)


class PullRequestCreateView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        form = PullRequestCreateForm()

        source_branch = request.GET.get("source", project.default_branch)
        target_branch = request.GET.get("target", project.default_branch)

        form.fields["source_branch"].initial = source_branch
        form.fields["target_branch"].initial = target_branch

        diffs = project.get_diff_between_branches(source_branch, target_branch)
        commits = project.get_commit_diff_between_refs(source_branch, target_branch)
        total_additions = sum(f["added_lines"] for f in diffs)
        total_deletions = sum(f["deleted_lines"] for f in diffs)

        context = {
            "project": project,
            "active_tab": "pull_requests",
            "form": form,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "diffs": diffs,
            "commits": commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
        }
        return render(request, "pull_requests/create.html", context)

    def post(self, request, *args, **kwargs):
        project = request.project
        form = PullRequestCreateForm(request.POST)
        if not form.is_valid():
            messages.error(
                request,
                "There was an error creating the pull request. Please check the form and try again.",
            )
            return redirect(
                "pull-request-list",
                username=project.owner.username,
                project_handle=project.handle,
            )

        cleaned_data = form.cleaned_data
        pull_request = PullRequest.objects.create(
            **cleaned_data,
            project=project,
            author=request.user,
            status=PullRequest.Status.OPEN,
        )

        return redirect(
            "pull-request-list",
            username=project.owner.username,
            project_handle=project.handle,
        )
