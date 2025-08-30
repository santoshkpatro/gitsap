from django.db import models
from django.db.models import Q

from gitsap.base.models import BaseModel


class Project(BaseModel):
    class Visibility(models.TextChoices):
        PUBLIC = ("public", "Public")
        PRIVATE = ("private", "Private")

    name = models.CharField(max_length=256)
    handle = models.SlugField(max_length=256, blank=True)
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    owner_user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="projects",
        blank=True,
        null=True,
    )
    owner_org = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="projects",
        blank=True,
        null=True,
    )

    default_branch = models.CharField(max_length=128, default="main")
    website = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
    )

    total_issues_count = models.IntegerField(default=0)
    repository = models.FileField(upload_to="repositories/", blank=True, null=True)

    class Meta:
        db_table = "projects"
        constraints = [
            models.UniqueConstraint(
                fields=["handle", "owner_user"],
                name="unique_user_project_handle",
                condition=Q(owner_user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["handle", "owner_org"],
                name="unique_org_project_handle",
                condition=Q(owner_org__isnull=False),
            ),
        ]

    @property
    def owner(self):
        return self.owner_user if self.owner_user else self.owner_org

    @property
    def owner_type(self):
        return "user" if self.owner_user else "organization"
