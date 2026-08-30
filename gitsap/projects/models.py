from django.db import models
from django.conf import settings

from gitsap.common.models import BaseCommonModel


class ProjectVisibility(models.TextChoices):
    PUBLIC = ("public", "Public")
    PRIVATE = ("private", "Private")
    INTERNAL = ("internal", "Internal")


class Project(BaseCommonModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_projects",
    )
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, blank=True)
    description = models.TextField(blank=True, null=True)

    repository_default_branch = models.CharField(max_length=128, default="main")
    repository_count = models.IntegerField(default=0)
    issue_count = models.IntegerField(default=0)
    pull_request_count = models.IntegerField(default=0)
    event_count = models.IntegerField(default=0)

    visibility = models.CharField(
        max_length=16,
        choices=ProjectVisibility.choices,
        default=ProjectVisibility.INTERNAL,
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="projects.ProjectMembership",
        through_fields=("project", "user"),
        related_name="projects",
    )

    class Meta:
        db_table = "projects"
        constraints = [
            models.UniqueConstraint(
                fields=["slug"],
                name="unique_project_slug",
            ),
        ]


class ProjectMembershipRole(models.TextChoices):
    OWNER = ("owner", "Owner")
    ADMIN = ("admin", "Admin")
    MAINTAINER = ("maintainer", "Maintainer")
    COLLABORATOR = ("collaborator", "Collaborator")
    GUEST = ("guest", "Guest")


class ProjectMembership(BaseCommonModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )
    role = models.CharField(
        max_length=16,
        choices=ProjectMembershipRole.choices,
        default=ProjectMembershipRole.COLLABORATOR,
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "project_memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_membership",
            ),
        ]


class ProjectInvitation(BaseCommonModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="invitations"
    )
    email_address = models.EmailField()
    role = models.CharField(
        max_length=16,
        choices=ProjectMembershipRole.choices,
        default=ProjectMembershipRole.COLLABORATOR,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="send_project_invitations",
    )
    token_hash = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField(blank=True)
    accepted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "project_invitations"
        constraints = [
            models.UniqueConstraint(
                fields=["token_hash"],
                name="unique_project_invitation_token_hash",
            ),
        ]
