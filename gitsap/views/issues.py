from django.views import View
from django.shortcuts import render

from gitsap.mixins import ProjectAccessMixin


class IssueListView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "issues"}
        return render(request, "issues/issue_list.html", context)


class IssueDetailView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "issues"}
        return render(request, "issues/issue_detail.html", context)


class IssueCreateView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "issues"}
        return render(request, "issues/issue_create.html", context)
