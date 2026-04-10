from django.db import models, transaction, IntegrityError
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError

from gitsap.models.shared import BaseModel
from gitsap.models.choices import ProjectVisibilityChoice, ProjectRoleChoice


class Project(BaseModel):
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.PROTECT,
        related_name="projects",
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )
    name = models.CharField(max_length=128)
    namespace = models.CharField(max_length=256, blank=True, unique=True)
    visibility = models.CharField(
        max_length=32,
        choices=ProjectVisibilityChoice.choices,
        default=ProjectVisibilityChoice.PRIVATE,
    )
    default_git_branch = models.CharField(max_length=128, default="main")
    about = models.TextField(blank=True, null=True)

    ID_PREFIX = "prj"

    class Meta:
        db_table = "projects"

    @classmethod
    def create(cls, *, created_by, name, visibility, organization=None):
        if organization:
            namespace = f"{organization.slug}/{slugify(name).lower()}"
        else:
            namespace = f"{created_by.username}/{slugify(name).lower()}"

        try:
            with transaction.atomic():
                new_project = cls.objects.create(
                    organization=organization,
                    created_by=created_by,
                    name=name,
                    visibility=visibility,
                    namespace=namespace,
                )
                if not organization:
                    new_project.permissions.create(
                        user=created_by,
                        role=ProjectRoleChoice.OWNER,
                    )

                return new_project
        except IntegrityError:
            raise ValidationError(
                {"namespace": "A project with this namespace already exists."}
            )
        except Exception:
            raise

    @property
    def repo_url(self):
        return f"{settings.APP_BASE_URL}/{self.namespace}.git"


class ProjectPermission(BaseModel):
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="permissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_permission",
    )
    role = models.CharField(
        max_length=32,
        choices=ProjectRoleChoice.choices,
        default=ProjectRoleChoice.DEVELOPER,
    )

    ID_PREFIX = "prp"

    class Meta:
        db_table = "project_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_user_permission",
            )
        ]
