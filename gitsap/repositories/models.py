from django.db import models
from django.conf import settings
from django.utils.text import slugify

from gitsap.common.models import BaseCommonModel


class Repository(BaseCommonModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="repositories"
    )
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, blank=True)
    description = models.TextField(blank=True, null=True)
    git_path = models.TextField(blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_repositories",
    )

    class Meta:
        db_table = "repositories"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "slug"], name="unique_project_name_slug"
            )
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.slug:
                self.slug = slugify(self.name)
        return super().save(*args, **kwargs)
