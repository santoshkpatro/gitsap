from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages

from projects.mixins import ProjectAccessMixin
from issues.models import Issue
from issues.forms import IssueCreateForm


class IssueListView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        issues = Issue.objects.filter(project=project).order_by("-created_at")
        context = {
            "issues": issues,
            "project": project,
            "active_tab": "issues",
        }
        return render(request, "issues/list.html", context)


class IssueCreateView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        form = IssueCreateForm()
        context = {
            "project": project,
            "active_tab": "issues",
            "form": form,
        }
        return render(request, "issues/create.html", context)

    def post(self, request, *args, **kwargs):
        project = request.project
        form = IssueCreateForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            context = {
                "form": form,
                "project": project,
                "active_tab": "issues",
            }
            return render(request, "issues/create.html", context)

        cleaned_data = form.cleaned_data
        issue = Issue(
            **cleaned_data,
            project=project,
            created_by=request.user,
        )
        issue.save()

        return redirect(
            "issue-detail",
            username=project.owner.username,
            project_handle=project.handle,
            issue_number=issue.issue_number,
        )


class IssueDetailView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        issue_number = kwargs.get("issue_number")
        issue = get_object_or_404(
            Issue,
            project=project,
            issue_number=issue_number,
        )

        context = {
            "issue": issue,
            "project": project,
            "active_tab": "issues",
        }
        return render(request, "issues/detail.html", context)
