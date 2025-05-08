import os, uuid, tarfile, pygit2, tempfile, subprocess
from pathlib import Path
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from datetime import datetime
from pathlib import Path

from shared.models import BaseUUIDModel

PROJECT_REPO_BASE = settings.BASE_DIR / "var"
GIT_OBJ_TYPE_MAP = {
    pygit2.GIT_OBJECT_COMMIT: "commit",
    pygit2.GIT_OBJECT_TREE: "tree",
    pygit2.GIT_OBJECT_BLOB: "blob",
    pygit2.GIT_OBJECT_TAG: "tag",
}


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

    def get_latest_commit_info(self, repo_path, relative_path):
        """
        Returns the latest commit info for a given file/directory path.

        Args:
            repo_path (str): Absolute path to the .git working tree (not .git folder).
            relative_path (str): Path relative to repo root (e.g., 'README.md').

        Returns:
            Optional[Dict]: A dictionary with commit hash, timestamp, and message.
        """
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%ct|%s", "--", relative_path],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True,
            )
            if result.stdout.strip():
                commit_hash, timestamp, message = result.stdout.strip().split("|", 2)
                return {
                    "hash": commit_hash,
                    "timestamp": datetime.fromtimestamp(int(timestamp)),
                    "message": message.strip(),
                }
        except subprocess.CalledProcessError:
            pass
        return None

    @property
    def root_tree_contents(self):
        """
        Returns the contents of the root tree of the project's default branch.

        Args:
            project (Project): An instance of the Project model.

        Returns:
            List[Dict]: A list of dictionaries with name, type, and id of each tree entry.
        """
        repo = self.repo  # pygit2.Repository instance
        branch_name = self.default_branch
        workdir = str(repo.path)  # .git is inside repo.path

        # Get the root commit of the default branch
        ref = repo.references.get(f"refs/heads/{branch_name}")
        if not ref:
            raise ValueError(f"Branch '{branch_name}' not found.")
        commit = repo[ref.target]
        tree = commit.tree

        # Sort: folders first, then alphabetically
        sorted_entries = sorted(
            tree, key=lambda e: (e.type != pygit2.GIT_OBJECT_TREE, e.name.lower())
        )

        results = []
        for entry in sorted_entries:
            path = entry.name
            latest_commit = self.get_latest_commit_info(workdir, path)

            results.append(
                {
                    "name": entry.name,
                    "type": GIT_OBJ_TYPE_MAP.get(entry.type, f"unknown({entry.type})"),
                    "id": str(entry.id),
                    "last_commit": latest_commit or {},
                }
            )
        return results

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
