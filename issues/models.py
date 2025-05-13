from django.db import models, transaction

from shared.models import BaseUUIDModel


class Issue(BaseUUIDModel):
    class Status(models.TextChoices):
        OPEN = ("open", "Open")
        CLOSED = ("closed", "Closed")

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="issues"
    )
    title = models.CharField(max_length=255)
    issue_number = models.IntegerField(blank=True)
    summary = models.TextField(blank=True, null=True)
    summary_html = models.TextField(blank=True, null=True)
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_issues",
    )
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.OPEN, db_index=True
    )

    assignees = models.ManyToManyField(
        "accounts.User",
        through="issues.IssueAssignee",
        related_name="issues_assigned",
    )

    class Meta:
        db_table = "issues"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "issue_number"], name="unique_issue_number"
            )
        ]

    def __str__(self):
        return str(self.title)

    def save(self, *args, **kwargs):
        if self._state.adding:
            last_issue = (
                Issue.objects.only("issue_number")
                .filter(project=self.project)
                .order_by("-issue_number")
                .first()
            )
            self.issue_number = (last_issue.issue_number + 1) if last_issue else 1
        return super().save(*args, **kwargs)

    @transaction.atomic
    def close(self):
        project = self.project
        self.status = Issue.Status.CLOSED
        self.save(update_fields=["status"])

        project.open_issues_count -= 1
        project.save(update_fields=["open_issues_count"])


class IssueAssignee(BaseUUIDModel):
    issue = models.ForeignKey(
        "issues.Issue", on_delete=models.CASCADE, related_name="issue_assignees"
    )
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="assigned_issues"
    )

    class Meta:
        db_table = "issues_assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "user"], name="unique_issue_assignee"
            )
        ]

    def __str__(self):
        return str(self.id)


class IssueActivity(BaseUUIDModel):
    class ActivityType(models.TextChoices):
        COMMENT = ("comment", "Comment")
        ACTION = ("action", "Action")

    issue = models.ForeignKey(
        "issues.Issue", on_delete=models.CASCADE, related_name="activities"
    )
    author = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="issue_activities"
    )
    activity_type = models.CharField(max_length=10, choices=ActivityType.choices)

    content = models.TextField(blank=True, null=True)
    content_html = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "issues_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)
