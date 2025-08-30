from django.db import models

from gitsap.base.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=128)
    handle = models.SlugField(max_length=128, unique=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
    )

    class Meta:
        db_table = "organizations"


class OrganizationMember(BaseModel):
    class Role(models.TextChoices):
        OWNER = ("owner", "Owner")
        ADMIN = ("admin", "Admin")
        MEMBER = ("member", "Member")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="organization_memberships"
    )
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        db_table = "organization_members"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="unique_organization_member"
            )
        ]
