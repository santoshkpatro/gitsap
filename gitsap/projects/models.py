import os, uuid, tarfile, pygit2, tempfile
from pathlib import Path
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from pathlib import Path

from gitsap.shared.models import BaseUUIDModel
from gitsap.git.service import GitService


class Project(BaseUUIDModel):
    class Visibility(models.TextChoices):
        PUBLIC = ("public", "Public")
        PRIVATE = ("private", "Private")
        INTERNAL = ("internal", "Internal")

    owner = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="projects"
    )

    # For easy access to the owner username
    owner_username = models.CharField(max_length=128, blank=True, db_index=True)

    name = models.CharField(max_length=128)
    handle = models.SlugField(max_length=128, blank=True)
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(choices=Visibility.choices, max_length=16)
    default_branch = models.CharField(max_length=128, default="main")

    resource_id = models.CharField(max_length=64, blank=True)
    resource = models.FileField(upload_to="projects_resources/", blank=True)

    total_issues_count = models.IntegerField(default=0)
    open_issues_count = models.IntegerField(default=0)

    total_pull_requests_count = models.IntegerField(default=0)
    open_pull_requests_count = models.IntegerField(default=0)
    merged_pull_requests_count = models.IntegerField(default=0)

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
            self.resource_id = uuid.uuid4().hex

            if not self.owner_username:
                self.owner_username = self.owner.username
        return super().save(*args, **kwargs)

    @property
    def ssh_clone_url(self):
        return f"{settings.SSH_GIT_HOST_URL}/{self.owner.username}/{self.handle}.git"

    @property
    def https_clone_url(self):
        return f"{settings.HTTPS_GIT_HOST_URL}/{self.owner.username}/{self.handle}.git"

    @property
    def closed_issues_count(self):
        return self.total_issues_count - self.open_issues_count

    @property
    def closed_pull_requests_count(self):
        return (
            self.total_pull_requests_count
            - self.open_pull_requests_count
            - self.merged_pull_requests_count
        )

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

    @property
    def git_service(self):
        return GitService(self._local_git_path)

    @property
    def repo_branches(self):
        branches = []
        for ref in self.repo.listall_references():
            if ref.startswith("refs/heads/"):
                branch_name = ref.removeprefix("refs/heads/")
                branches.append(branch_name)
        return branches

    @property
    def repo_tags(self):
        tags = []
        for ref in self.repo.listall_references():
            if ref.startswith("refs/tags/"):
                tag_name = ref.removeprefix("refs/tags/")
                tags.append(tag_name)
        return tags

    @property
    def _local_git_path(self):
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

        return str((Path(repo_dir)).resolve())

    def _setup_cloud_resource_artifact(self):
        # Step 1: Create local bare repo at var/git-repos/{pk}.git
        repo_id = f"{self.pk}.git"
        repo_dir = settings.BASE_DIR / "var" / "git-repos" / repo_id
        os.makedirs(repo_dir, exist_ok=True)
        pygit2.init_repository(str(repo_dir), bare=True)

        # Step 2: Create tar.gz archive of its contents (not the folder itself)
        s3_key = f"project_resources/{self.resource_id}_{int(timezone.now().timestamp())}.tar.gz"

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

    def update_cloud_resource_artifact(self):
        repo_id = f"{self.pk}.git"
        repo_dir = settings.BASE_DIR / "var" / "git-repos" / repo_id

        # Step 1: Create tar.gz archive of its contents (not the folder itself)
        s3_key = f"project_resources/{self.resource_id}_{int(timezone.now().timestamp())}.tar.gz"

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)

            with tarfile.open(tmp_file_path, "w:gz") as tar:
                for item in repo_dir.iterdir():
                    tar.add(item, arcname=item.name)
                # Zip contents only, not .git folder
            # Step 2: Upload to S3
            settings.S3_CLIENT.upload_file(
                Filename=str(tmp_file_path),
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=s3_key,
            )
        # Step 3: Clean up local temp file
        tmp_file_path.unlink(missing_ok=True)
        # Step 4: Save to model
        self.resource.name = s3_key
        self.save(update_fields=["resource"])


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
