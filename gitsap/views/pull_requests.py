from django.views import View
from django.shortcuts import render

from gitsap.mixins import ProjectAccessMixin


class PullRequestListView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pull_requests"}
        return render(request, "pull_requests/pull_request_list.html", context)


class PullRequestDetailView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pull_requests"}
        return render(request, "pull_requests/pull_request_detail.html", context)


class PullRequestCreateView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pull_requests"}
        return render(request, "pull_requests/pull_request_create.html", context)


class PullRequestConfirmView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "pull_requests"}
        return render(request, "pull_requests/pull_request_confirm.html", context)
