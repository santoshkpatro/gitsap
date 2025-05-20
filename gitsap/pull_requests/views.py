from collections import defaultdict
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q

from gitsap.projects.mixins import ProjectAccessMixin
from gitsap.pull_requests.forms import (
    PullRequestCreateForm,
    PullRequestMergeConfirmForm,
)
from gitsap.pull_requests.models import PullRequest, PullRequestActivity


class PullRequestListView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        status = request.GET.get("status", "open")
        if status == "all":
            status_filter = Q(status__in=["open", "closed", "merged"])
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
        git_service = project.git_service
        source_branch = request.GET.get("source", project.default_branch)
        target_branch = request.GET.get("target", project.default_branch)

        diffs = git_service.get_diff_between_branches(source_branch, target_branch)
        commits = git_service.get_commit_diff_between_refs(source_branch, target_branch)
        total_additions = sum(f["added_lines"] for f in diffs)
        total_deletions = sum(f["deleted_lines"] for f in diffs)
        conflicts = git_service.get_merge_conflicts(source_branch, target_branch)

        context = {
            "project": project,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "diffs": diffs,
            "conflicts": conflicts,
            "commits": commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "active_tab": "pull_requests",
        }
        return render(request, "pull_requests/compare.html", context)


class PullRequestCreateView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        git_service = project.git_service
        form = PullRequestCreateForm()

        source_branch = request.GET.get("source", project.default_branch)
        target_branch = request.GET.get("target", project.default_branch)

        form.fields["source_branch"].initial = source_branch
        form.fields["target_branch"].initial = target_branch

        diffs = git_service.get_diff_between_branches(source_branch, target_branch)
        commits = git_service.get_commit_diff_between_refs(source_branch, target_branch)
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
                username=project.owner_username,
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
            username=project.owner_username,
            project_handle=project.handle,
        )


class PullRequestDetailView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        git_service = project.git_service

        pull_request_number = kwargs.get("pull_request_number")
        pull_request = PullRequest.objects.get(
            project=project, pull_request_number=pull_request_number
        )
        current_tab = request.GET.get("tab", "activity")
        default_commit_message = f"Merge pull request #{pull_request.pull_request_number} from {pull_request.source_branch}"
        pr_merge_form = PullRequestMergeConfirmForm()
        pr_merge_form.fields["commit_message"].initial = default_commit_message
        context = {
            "project": project,
            "pull_request": pull_request,
            "current_tab": current_tab,
            "default_commit_message": default_commit_message,
            "active_tab": "pull_requests",
            "pr_merge_form": pr_merge_form,
        }
        match current_tab:
            case "activity":
                activities = (
                    PullRequestActivity.objects.filter(pull_request=pull_request)
                    .order_by("-created_at")
                    .select_related("author")
                )
                conflicts = git_service.get_merge_conflicts(
                    pull_request.source_branch, pull_request.target_branch
                )
                context["activities"] = activities
                context["conflicts"] = conflicts
            case "commits":
                commits = git_service.get_commit_diff_between_refs(
                    pull_request.source_branch, pull_request.target_branch
                )
                grouped_commits = defaultdict(list)
                for commit in commits:
                    local_date = commit["timestamp"].date()
                    grouped_commits[local_date].append(commit)

                context["grouped_commits"] = dict(grouped_commits)
            case "changes":
                diffs = git_service.get_diff_between_branches(
                    pull_request.source_branch, pull_request.target_branch
                )
                context["diffs"] = diffs
            case _:
                messages.error(request, "Invalid tab selected.")
                return redirect(
                    "pull-request-detail",
                    username=project.owner_username,
                    project_handle=project.handle,
                    pull_request_number=pull_request_number,
                )
        return render(request, "pull_requests/detail.html", context)


class PullRequestMergeView(ProjectAccessMixin, View):
    def post(self, request, *args, **kwargs):
        project = request.project
        git_service = project.git_service
        pull_request_number = kwargs.get("pull_request_number")

        form = PullRequestMergeConfirmForm(request.POST)
        if not form.is_valid():
            messages.error(
                request,
                "There was an error merging the pull request. Please check the form and try again.",
            )
            return redirect(
                "pull-request-detail",
                username=project.owner_username,
                project_handle=project.handle,
                pull_request_number=pull_request_number,
            )

        pull_request = PullRequest.objects.get(
            project=project,
            pull_request_number=pull_request_number,
        )

        if pull_request.status == PullRequest.Status.MERGED:
            messages.error(request, "This pull request has already been merged.")
            return redirect(
                "pull-request-detail",
                username=project.owner_username,
                project_handle=project.handle,
                pull_request_number=pull_request_number,
            )

        cleaned_data = form.cleaned_data
        commit_message = cleaned_data.get(
            "commit_message",
            f"Merge pull request #{pull_request.pull_request_number} from {pull_request.source_branch}",
        )

        # Attempt merge
        response = git_service.merge_branches(
            source_branch=pull_request.source_branch,
            target_branch=pull_request.target_branch,
            user_name=request.user.name,
            user_email=request.user.email,
            commit_message=commit_message,
        )

        if not response.get("merged"):
            if response.get("conflicts"):
                messages.error(request, "Merge failed due to conflicts.")
            elif response.get("error"):
                messages.error(request, f"Merge failed: {response['error']}")
            else:
                messages.error(request, "Merge failed for unknown reasons.")

            return redirect(
                "pull-request-detail",
                username=project.owner_username,
                project_handle=project.handle,
                pull_request_number=pull_request_number,
            )

        # If merge is successful
        pull_request.merge()  # mark PR as merged
        project.update_cloud_resource_artifact()  # upload updated git tar

        messages.success(request, "Pull request merged successfully.")
        return redirect(
            "pull-request-detail",
            username=project.owner_username,
            project_handle=project.handle,
            pull_request_number=pull_request_number,
        )


class PullRequestConflictsView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        pull_request_number = kwargs.get("pull_request_number")
        pull_request = PullRequest.objects.get(
            project=project, pull_request_number=pull_request_number
        )
        conflicts = project.get_merge_conflicts(
            pull_request.source_branch, pull_request.target_branch
        )

        conflict_files = []
        for conflict in conflicts:
            conflict_files.append(
                {
                    "file_path": conflict["path"],
                    "conflict_lines": project.get_conflict_lines(
                        conflict["ours"],
                        conflict["theirs"],
                        pull_request.source_branch,
                        pull_request.target_branch,
                    ),
                }
            )

        context = {
            "project": project,
            "pull_request": pull_request,
            "conflict_files": conflict_files,
            "active_tab": "pull_requests",
        }
        return render(request, "pull_requests/conflicts.html", context)
