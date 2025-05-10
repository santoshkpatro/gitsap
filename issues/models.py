from django.db import models

from shared.models import BaseUUIDModel


class Issue(BaseUUIDModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="issues"
    )
    title = models.CharField(max_length=255)
    issue_number = models.IntegerField(blank=True)
    summary = models.TextField()
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_issues",
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
    content = models.TextField()

    class Meta:
        db_table = "issues_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)
