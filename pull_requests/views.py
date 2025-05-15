from django.shortcuts import render
from django.views import View

from projects.mixins import ProjectAccessMixin


class PullRequestCreateView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        # Render the pull request creation form
        return render(request, "pull_requests/create.html", {})
