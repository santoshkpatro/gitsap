from django.db import models

from shared.models import BaseUUIDModel


class Project(BaseUUIDModel):
    class Visibility(models.TextChoices):
        PUBLIC = ("public", "Public")
        PRIVATE = ("private", "Private")
        INTERNAL = ("internal", "Internal")

    owner = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=128)
    handle = models.SlugField(max_length=128)
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(choices=Visibility.choices, max_length=16)
    default_branch = models.CharField(max_length=128, default="main")
    resource = models.FileField(upload_to="projects/resources/", blank=True)

    collaborators = models.ManyToManyField(
        "accounts.User", through="ProjectCollaborator"
    )

    class Meta:
        db_table = "projects"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "handle"], name="unique_project_handle"
            )
        ]

    def __str__(self):
        return f"{self.name}"


class ProjectCollaborator(BaseUUIDModel):
    class Role(models.TextChoices):
        OWNER = ("owner", "Owner")
        COLLABORATOR = ("collaborator", "Collaborator")

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="project_collaborators"
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="user_project_collaborators",
    )
    role = models.CharField(choices=Role.choices, max_length=16)

    class Meta:
        db_table = "project_collaborators"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"], name="unique_project_collaborator"
            )
        ]

    def __str__(self):
        return f"{str(self.id)}"
