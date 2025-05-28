import markdown
from django.db import models, transaction

from gitsap.shared.models import BaseUUIDModel


class PullRequest(BaseUUIDModel):
    class Status(models.TextChoices):
        OPEN = ("open", "Open")
        CLOSED = ("closed", "Closed")
        MERGED = ("merged", "Merged")

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="pull_requests"
    )
    title = models.CharField(max_length=255)
    pull_request_number = models.IntegerField(blank=True)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_pull_requests",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    source_branch = models.CharField(max_length=255)
    target_branch = models.CharField(max_length=255)

    class Meta:
        db_table = "pull_requests"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "pull_request_number"],
                name="unique_pull_request_number",
            ),
            models.UniqueConstraint(
                fields=["project", "source_branch", "target_branch"],
                condition=models.Q(status="open"),
                name="unique_open_pull_request_per_branch_pair",
            ),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            last_pull_request = (
                PullRequest.objects.only("pull_request_number")
                .filter(project=self.project)
                .order_by("-pull_request_number")
                .first()
            )
            self.pull_request_number = (
                last_pull_request.pull_request_number + 1 if last_pull_request else 1
            )
        return super().save(*args, **kwargs)

    @transaction.atomic
    def merge(self):
        project = self.project

        self.status = self.Status.MERGED
        self.save(update_fields=["status"])

        project.open_pull_requests_count -= 1
        project.merged_pull_requests_count += 1

        project.save(
            update_fields=["open_pull_requests_count", "merged_pull_requests_count"]
        )


class PullRequestAssignee(BaseUUIDModel):
    pull_request = models.ForeignKey(
        "pull_requests.PullRequest",
        on_delete=models.CASCADE,
        related_name="pull_request_assignees",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="pull_request_assignees",
    )

    class Meta:
        db_table = "pull_request_assignees"
        constraints = [
            models.UniqueConstraint(
                fields=["pull_request", "user"], name="unique_pull_request_assignee"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)


class PullRequestActivity(BaseUUIDModel):
    class ActivityType(models.TextChoices):
        COMMENT = ("comment", "Comment")
        ACTION = ("action", "Action")

    pull_request = models.ForeignKey(
        "pull_requests.PullRequest",
        on_delete=models.CASCADE,
        related_name="activities",
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="pull_request_activities",
    )
    activity_type = models.CharField(max_length=10, choices=ActivityType.choices)
    content = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "pull_request_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)

    @property
    def content_html(self):
        raw_html = markdown.markdown(self.content or "", extensions=["nl2br"])
        if self.activity_type == self.ActivityType.ACTION:
            # Remove <p> tags for inline rendering
            return raw_html.removeprefix("<p>").removesuffix("</p>").strip()
        return raw_html