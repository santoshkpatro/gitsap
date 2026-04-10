from django.db import models
from django.conf import settings

from gitsap.models.shared import BaseModel
from gitsap.models.choices import OrganizationPermissionChoice


class Organization(BaseModel):
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, blank=True, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
    )
    url = models.URLField(blank=True, null=True)
    contact_email = models.EmailField()

    ID_PREFIX = "org"

    class Meta:
        db_table = "organizations"


class OrganizationPermission(BaseModel):
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="permissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_permissions",
    )
    role = models.CharField(
        max_length=16,
        choices=OrganizationPermissionChoice.choices,
        default=OrganizationPermissionChoice.COLLABORATOR,
    )

    ID_PREFIX = "orp"

    class Meta:
        db_table = "organization_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="uniq_user_permission_per_org"
            )
        ]
