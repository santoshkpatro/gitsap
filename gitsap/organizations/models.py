from django.db import models
from django.utils.text import slugify

from gitsap.shared.models import BaseUUIDModel


class Organization(BaseUUIDModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    members = models.ManyToManyField(
        "accounts.User",
        through="organizations.OrganizationUser",
        related_name="organizations",
    )

    class Meta:
        db_table = "organizations"
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.slug:
                self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class OrganizationUser(BaseUUIDModel):
    class Role(models.TextChoices):
        OWNER = ("owner", "Owner")
        ADMIN = ("admin", "Admin")
        MAINTAINER = ("maintainer", "Maintainer")
        DEVELOPER = ("developer", "Developer")

    organization = models.ForeignKey(
        "organizations.Organization", related_name="users", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "accounts.User", related_name="organization_users", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.ADMIN)

    class Meta:
        db_table = "organization_users"
        verbose_name = "Organization User"
        verbose_name_plural = "Organization Users"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="unique_organization_user"
            )
        ]

    def __str__(self):
        return f"{str(self.id)}"
