from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from gitsap.base.models import BaseModel


class Project(BaseModel):
    class Visibility(models.TextChoices):
        PUBLIC = ("public", "Public")
        PRIVATE = ("private", "Private")

    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=256, blank=True)
    namespace = models.SlugField(max_length=512, blank=True, unique=True)
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

    collaborators = models.ManyToManyField(
        "users.User",
        related_name="collaborations",
        through="projects.ProjectPermission",
    )

    class Meta:
        db_table = "projects"
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "owner_user"],
                name="unique_user_project_handle",
                condition=Q(owner_user__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["slug", "owner_org"],
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

    def _generate_slug(self):
        """Generate slug and ensure uniqueness for the given owner."""
        if not self.slug:
            self.slug = slugify(self.name)

        # Check for slug uniqueness under same owner
        if (
            self.owner_user
            and Project.objects.filter(
                slug=self.slug, owner_user=self.owner_user
            ).exists()
        ):
            raise ValidationError(
                f"A project with slug '{self.slug}' already exists for this user."
            )

        if (
            self.owner_org
            and Project.objects.filter(
                slug=self.slug, owner_org=self.owner_org
            ).exists()
        ):
            raise ValidationError(
                f"A project with slug '{self.slug}' already exists for this organization."
            )

    def _generate_namespace(self):
        """Generate namespace and ensure global uniqueness."""
        if self.owner_user:
            base = self.owner_user.username
        elif self.owner_org:
            base = self.owner_org.slug
        else:
            raise ValueError("Project must have either an user or organization")

        self.namespace = f"{base}/{self.slug}"

        # Check for namespace uniqueness
        if Project.objects.filter(namespace=self.namespace).exists():
            raise ValidationError(
                f"A project with namespace '{self.namespace}' already exists."
            )

    def save(self, *args, **kwargs):
        """Generate slug + namespace before saving, rely on DB for unique checks."""
        if self._state.adding or not self.slug or not self.namespace:
            self._generate_slug()
            self._generate_namespace()

        super().save(*args, **kwargs)

    @classmethod
    def initialize(
        cls, *, name, owner_user=None, owner_org=None, created_by=None, **kwargs
    ):
        """Safe constructor: returns (project_or_none, [errors])."""
        project = cls(
            name=name,
            owner_user=owner_user,
            owner_org=owner_org,
            created_by=created_by,
            **kwargs,
        )

        try:
            with transaction.atomic():
                project.save()
            return project, []
        except ValidationError as e:
            # Collect field / non-field errors in a readable list
            if hasattr(e, "message_dict"):
                # ValidationError with field-wise messages
                errors = [
                    f"{field}: {', '.join(msgs)}"
                    for field, msgs in e.message_dict.items()
                ]
            else:
                errors = e.messages if hasattr(e, "messages") else [str(e)]
            return None, errors
        except IntegrityError as e:
            return None, [f"Database integrity error: {str(e)}"]
        except ValueError as e:
            return None, [f"Value error: {str(e)}"]
        except Exception as e:
            # Last safety net — avoid leaking raw stack trace
            return None, [f"Unexpected error: {str(e)}"]


class ProjectPermission(BaseModel):
    class Role(models.TextChoices):
        READ = ("read", "Read")
        TRIAGE = ("triage", "Triage")
        WRITE = ("write", "Write")
        MAINTAIN = ("maintain", "Maintain")
        ADMIN = ("admin", "Admin")
        OWNER = ("owner", "Owner")

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="permissions"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="project_permissions"
    )
    role = models.CharField(max_length=12, choices=Role.choices)

    class Meta:
        db_table = "project_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"], name="unique_project_user_permission"
            )
        ]
