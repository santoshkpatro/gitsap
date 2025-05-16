from django.shortcuts import render
from django.views import View

from projects.mixins import ProjectAccessMixin


class PullRequestCompareView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        source_branch = request.GET.get("source", project.default_branch)
        target_branch = request.GET.get("target", project.default_branch)

        diffs = project.get_diff_between_branches(source_branch, target_branch)

        context = {
            "project": project,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "diffs": diffs,
            "active_tab": "pull_requests",
        }
        return render(request, "pull_requests/compare.html", context)
