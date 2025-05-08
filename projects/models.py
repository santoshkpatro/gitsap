import os, uuid, tarfile, pygit2, tempfile
from pathlib import Path
from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import File
from django.conf import settings
from django.utils.text import slugify

from shared.models import BaseUUIDModel

PROJECT_REPO_BASE = settings.BASE_DIR / "var"


class Project(BaseUUIDModel):
    class Visibility(models.TextChoices):
        PUBLIC = ("public", "Public")
        PRIVATE = ("private", "Private")
        INTERNAL = ("internal", "Internal")

    owner = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=128)
    handle = models.SlugField(max_length=128, blank=True)
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(choices=Visibility.choices, max_length=16)
    default_branch = models.CharField(max_length=128, default="main")
    resource = models.FileField(upload_to="projects_resources/", blank=True)

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

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.handle = slugify(self.name)
        return super().save(*args, **kwargs)

    def _setup_cloud_resource_artifact(self):
        # Step 1: Create local bare repo at var/git-repos/{pk}.git
        repo_id = f"{self.pk}.git"
        repo_dir = settings.BASE_DIR / "var" / "git-repos" / repo_id
        os.makedirs(repo_dir, exist_ok=True)
        pygit2.init_repository(str(repo_dir), bare=True)

        # Step 2: Create tar.gz archive of its contents (not the folder itself)
        path_uuid = uuid.uuid4().hex
        s3_key = f"project_resources/{path_uuid}.tar.gz"

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)

            with tarfile.open(tmp_file_path, "w:gz") as tar:
                for item in repo_dir.iterdir():
                    tar.add(
                        item, arcname=item.name
                    )  # Zip contents only, not .git folder

            # Step 3: Upload to S3
            settings.S3_CLIENT.upload_file(
                Filename=str(tmp_file_path),
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=s3_key,
            )

        # Step 4: Clean up local temp file
        tmp_file_path.unlink(missing_ok=True)

        # Step 5: Save to model
        self.resource.name = s3_key
        self.save(update_fields=["resource"])

    @property
    def repo(self):
        repo_dir = settings.BASE_DIR / "var" / "git-repos" / f"{self.pk}.git"

        if not repo_dir.exists():
            # Step 1: Create parent directory if needed
            repo_dir.parent.mkdir(parents=True, exist_ok=True)

            # Step 2: Download the tar.gz from S3 to temp file
            with tempfile.NamedTemporaryFile(
                suffix=".tar.gz", delete=False
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)

                settings.S3_CLIENT.download_file(
                    settings.AWS_STORAGE_BUCKET_NAME,
                    self.resource.name,  # e.g., "project_resources/uuid.tar.gz"
                    str(tmp_path),
                )

            # Step 3: Extract contents into repo_dir
            repo_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(tmp_path, "r:gz") as tar:
                tar.extractall(path=repo_dir)

            # Step 4: Cleanup
            tmp_path.unlink(missing_ok=True)

        # Step 5: Return pygit2.Repository instance
        return pygit2.Repository(str(repo_dir))


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
