from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.db.models import Q

from gitsap.projects.mixins import ProjectAccessMixin
from gitsap.issues.models import Issue, IssueActivity, IssueAssignee
from gitsap.issues.forms import IssueCreateForm, IssueCommentCreateForm


class IssueListView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")

        project = request.project
        status = request.GET.get("status", "open")
        if status == "all":
            status_filter = Q(status__in=["open", "closed"])
        else:
            status_filter = Q(status=status)
        issues = (
            Issue.objects.filter(project=project)
            .filter(status_filter)
            .order_by("-issue_number")
        )
        context = {
            "issues": issues,
            "project": project,
            "active_tab": "issues",
            "status": status,
        }
        return render(request, "issues/list.html", context)


class IssueCreateView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_write")

        project = request.project
        form = IssueCreateForm()
        form.fields["assignees"].queryset = project.collaborators.all()
        context = {
            "project": project,
            "active_tab": "issues",
            "form": form,
        }
        return render(request, "issues/create.html", context)

    def post(self, request, *args, **kwargs):
        self.require_permission(request, "can_write")

        project = request.project
        form = IssueCreateForm(request.POST)
        form.fields["assignees"].queryset = project.collaborators.all()

        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            context = {
                "form": form,
                "project": project,
                "active_tab": "issues",
            }
            return render(request, "issues/create.html", context)

        cleaned_data = form.cleaned_data
        assignees = cleaned_data.pop("assignees", [])
        issue = Issue(
            **cleaned_data,
            project=project,
            author=request.user,
        )
        issue.save()
        for assignee in assignees:
            IssueAssignee.objects.create(
                issue=issue,
                user=assignee,
            )

        return redirect(
            "issue-detail",
            namespace=project.namespace,
            handle=project.handle,
            issue_number=issue.issue_number,
        )


class IssueDetailView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")

        project = request.project
        issue_number = kwargs.get("issue_number")
        issue = get_object_or_404(
            Issue,
            project=project,
            issue_number=issue_number,
        )
        activities = (
            IssueActivity.objects.filter(issue=issue)
            .order_by("created_at")
            .select_related("author")
        )
        assignees = issue.assignees.all()

        context = {
            "issue": issue,
            "project": project,
            "active_tab": "issues",
            "activities": activities,
            "assignees": assignees,
        }
        return render(request, "issues/detail.html", context)


class IssueCloseView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_write")

        issue_number = kwargs.get("issue_number")
        issue = get_object_or_404(
            Issue,
            project=request.project,
            issue_number=issue_number,
        )
        if issue.status == Issue.Status.CLOSED:
            messages.error(request, "Issue is already closed.")
        else:
            issue.close()
            IssueActivity.objects.create(
                issue=issue,
                author=request.user,
                activity_type=IssueActivity.ActivityType.ACTION,
                content="*closed* the issue.",
            )
            messages.success(request, "Issue closed successfully.")
        return redirect(
            "issue-detail",
            namespace=request.project.namespace,
            handle=request.project.handle,
            issue_number=issue_number,
        )


class IssueReOpenView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_write")

        issue_number = kwargs.get("issue_number")
        issue = get_object_or_404(
            Issue,
            project=request.project,
            issue_number=issue_number,
        )
        if issue.status == Issue.Status.OPEN:
            messages.error(request, "Issue is already open.")
        else:
            issue.re_open()
            IssueActivity.objects.create(
                issue=issue,
                author=request.user,
                activity_type=IssueActivity.ActivityType.ACTION,
                content="*reopened* the issue.",
            )
            messages.success(request, "Issue reopened successfully.")
        return redirect(
            "issue-detail",
            namespace=request.project.namespace,
            handle=request.project.handle,
            issue_number=issue_number,
        )


class IssueCommentCreateView(ProjectAccessMixin, View):
    def post(self, request, *args, **kwargs):
        self.require_permission(request, "can_write")

        issue_number = kwargs.get("issue_number")
        issue = get_object_or_404(
            Issue,
            project=request.project,
            issue_number=issue_number,
        )
        form = IssueCommentCreateForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return redirect(
                "issue-detail",
                namespace=request.project.namespace,
                handle=request.project.handle,
                issue_number=kwargs.get("issue_number"),
            )

        cleaned_data = form.cleaned_data
        IssueActivity.objects.create(
            **cleaned_data,
            issue=issue,
            author=request.user,
            activity_type=IssueActivity.ActivityType.COMMENT,
        )
        messages.success(request, "Comment added successfully.")
        return redirect(
            "issue-detail",
            namespace=request.project.namespace,
            handle=request.project.handle,
            issue_number=issue_number,
        )
