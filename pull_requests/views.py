from django.shortcuts import render
from django.views import View

from projects.mixins import ProjectAccessMixin


class PullRequestListView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        pull_requests = project.pull_requests.all()
        context = {
            "project": project,
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
