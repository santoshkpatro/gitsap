import os, uuid, tarfile, pygit2, tempfile, subprocess
from pathlib import Path
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from datetime import datetime
from pathlib import Path

from shared.models import BaseUUIDModel

GIT_OBJ_TYPE_MAP = {
    pygit2.GIT_OBJECT_COMMIT: "commit",
    pygit2.GIT_OBJECT_TREE: "tree",
    pygit2.GIT_OBJECT_BLOB: "blob",
    pygit2.GIT_OBJECT_TAG: "tag",
}
EXTENSION_MAP = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "jsx": "jsx",
    "tsx": "tsx",
    "json": "json",
    "html": "markup",  # Prism uses 'markup' for HTML/XML
    "xml": "markup",
    "css": "css",
    "scss": "scss",
    "sh": "bash",
    "bash": "bash",
    "yml": "yaml",
    "yaml": "yaml",
    "md": "markdown",
    "php": "php",
    "go": "go",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "rb": "ruby",
    "rs": "rust",
    "toml": "toml",
    "swift": "swift",
    "dockerfile": "docker",
    "gitignore": "git",
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

    resource_id = models.CharField(max_length=64, blank=True)
    resource = models.FileField(upload_to="projects_resources/", blank=True)

    total_issues_count = models.IntegerField(default=0)
    open_issues_count = models.IntegerField(default=0)

    total_pull_requests_count = models.IntegerField(default=0)
    open_pull_requests_count = models.IntegerField(default=0)

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

    @property
    def root_tree_objects(self):
        repo = self.repo
        branch_name = self.default_branch
        workdir = str(repo.path)

        ref = repo.references.get(f"refs/heads/{branch_name}")
        if not ref:
            return []  # No commits yet

        commit = repo[ref.target]
        tree = commit.tree

        sorted_entries = sorted(
            tree, key=lambda e: (e.type != pygit2.GIT_OBJECT_TREE, e.name.lower())
        )

        results = []
        for entry in sorted_entries:
            path = entry.name
            latest_commit = self.get_last_commit_info(path, branch_name)
            results.append(
                {
                    "name": entry.name,
                    "type": GIT_OBJ_TYPE_MAP.get(entry.type, f"unknown({entry.type})"),
                    "id": str(entry.id),
                    "last_commit": latest_commit or {},
                }
            )
        return results

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

    def get_last_commit_info(self, relative_path, branch):
        try:
            ref = f"refs/heads/{branch}"
            cmd = [
                "git",
                "log",
                "-1",
                "--format=%H|%ct|%s|%an|%ae",
                ref,
            ]

            # Only add the path if it's provided
            if relative_path:
                cmd += ["--", relative_path]

            result = subprocess.run(
                cmd,
                cwd=self._local_git_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                commit_hash, timestamp, message, author_name, author_email = (
                    result.stdout.strip().split("|", 4)
                )
                return {
                    "hash": commit_hash,
                    "timestamp": datetime.fromtimestamp(int(timestamp)),
                    "message": message.strip(),
                    "author_name": author_name,
                    "author_email": author_email,
                }
        except subprocess.CalledProcessError as e:
            print("Error:", e)
        return None

    def get_tree_objects_at_path(self, ref_name, relative_path):
        repo = self.repo
        workdir = str(repo.path)

        # Resolve ref to commit
        ref = repo.references.get(f"refs/heads/{ref_name}")
        if not ref:
            return []

        commit = repo[ref.target]
        tree = commit.tree

        # Traverse to the correct sub-tree based on the relative path
        parts = relative_path.strip("/").split("/") if relative_path else []
        for part in parts:
            try:
                entry = tree[part]
                if entry.type != pygit2.GIT_OBJECT_TREE:
                    return []  # Not a directory
                tree = repo[entry.id]
            except KeyError:
                return []  # Path does not exist

        # Sort: trees first, then blobs
        sorted_entries = sorted(
            tree, key=lambda e: (e.type != pygit2.GIT_OBJECT_TREE, e.name.lower())
        )

        results = []
        for entry in sorted_entries:
            path = os.path.join(relative_path, entry.name)
            latest_commit = self.get_last_commit_info(path, ref_name)
            results.append(
                {
                    "name": entry.name,
                    "type": GIT_OBJ_TYPE_MAP.get(entry.type, f"unknown({entry.type})"),
                    "id": str(entry.id),
                    "last_commit": latest_commit or {},
                }
            )
        return results

    def get_blob_at_path(self, ref_name: str, relative_path: str):
        repo = self.repo

        # Step 1: Resolve the branch or ref
        ref = repo.references.get(f"refs/heads/{ref_name}")
        if not ref:
            return None

        commit = repo[ref.target]
        tree = commit.tree
        workdir = str(repo.path)

        # Step 2: Traverse to the file
        parts = relative_path.strip("/").split("/")
        for part in parts[:-1]:
            try:
                tree_entry = tree[part]
                if tree_entry.type != pygit2.GIT_OBJECT_TREE:
                    return None
                tree = repo[tree_entry.id]
            except KeyError:
                return None

        # Step 3: Get the final blob
        try:
            blob_entry = tree[parts[-1]]
            if blob_entry.type != pygit2.GIT_OBJECT_BLOB:
                return None
            blob = repo[blob_entry.id]
            content = blob.data
            encoding = "utf-8" if b"\0" not in content else "binary"

            last_commit = self.get_last_commit_info(relative_path, ref_name)
            file_ext = relative_path.split(".")[-1]

            return {
                "name": parts[-1],
                "id": str(blob.id),
                "size": blob.size,
                "content": content,
                "encoding": encoding,
                "code": content.decode(encoding, errors="replace"),
                "language": EXTENSION_MAP.get(file_ext, "plaintext"),
                "last_commit": last_commit or {},
            }
        except KeyError:
            return None

    def get_last_commit_info_for_ref(self, ref_name: str):
        try:
            repo = self.repo

            # Support both heads (branches) and tags
            ref = repo.references.get(f"refs/heads/{ref_name}") or repo.references.get(
                f"refs/tags/{ref_name}"
            )
            if not ref:
                return None

            commit = repo[ref.target]
            return {
                "hash": str(commit.id),
                "timestamp": datetime.fromtimestamp(commit.commit_time),
                "message": commit.message.strip(),
                "author_name": commit.author.name,
                "author_email": commit.author.email,
            }
        except Exception as e:
            print("Error in get_last_commit_info_for_ref:", e)
            return None

    def resolve_ref_and_path(self, ref_and_path: str) -> tuple[str, str]:
        repo = self.repo
        parts = ref_and_path.strip("/").split("/")

        for i in range(len(parts), 0, -1):
            candidate_ref = "/".join(parts[:i])
            try:
                # Try resolving the candidate as a ref
                obj = repo.revparse_single(candidate_ref)
                if obj.type == pygit2.GIT_OBJECT_COMMIT:
                    relative_path = "/".join(parts[i:])
                    return candidate_ref, relative_path
            except (KeyError, pygit2.GitError):
                continue

        raise ValueError("Unable to resolve ref from path")

    def get_commits_count(self, ref_name: str):
        repo = self.repo
        ref = repo.references.get(f"refs/heads/{ref_name}")
        if not ref:
            return 0

        commit = repo[ref.target]
        commits_count = 0
        for _ in repo.walk(commit.id, pygit2.GIT_SORT_NONE):
            commits_count += 1

        return commits_count

    def get_commit_history(self, ref_name: str, max_count: int = 50, skip: int = 0):
        """
        Get commit history for a given ref/branch.
        Supports pagination using `skip` to offset the number of commits.
        """
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"refs/heads/{ref_name}",
                    f"--skip={skip}",
                    f"-n{max_count}",
                    "--format=%H|%ct|%s|%an|%ae",
                ],
                cwd=self._local_git_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # <- Show stderr if needed
                text=True,
                check=True,
            )

            history = []
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    commit_hash, timestamp, message, author_name, author_email = (
                        line.split("|", 4)
                    )
                    history.append(
                        {
                            "hash": commit_hash,
                            "timestamp": datetime.fromtimestamp(int(timestamp)),
                            "message": message.strip(),
                            "author_name": author_name,
                            "author_email": author_email,
                        }
                    )
                except ValueError:
                    continue  # skip malformed lines

            return history

        except subprocess.CalledProcessError as e:
            print("Git log error:", e.stderr)
            return []

    def get_diff_between_branches(self, source_branch: str, target_branch: str):
        repo = self.repo

        try:
            source_commit = repo.revparse_single(f"refs/heads/{source_branch}")
            target_commit = repo.revparse_single(f"refs/heads/{target_branch}")
        except KeyError:
            return {"error": "One or both branches not found"}

        source_tree = source_commit.tree
        target_tree = target_commit.tree
        diff = repo.diff(target_tree, source_tree, context_lines=3)

        changes = []
        for patch in diff:
            delta = patch.delta
            new_path = delta.new_file.path
            status = delta.status_char()

            lines = []
            added_lines = deleted_lines = 0

            for hunk in patch.hunks:
                old_lineno = hunk.old_start
                new_lineno = hunk.new_start

                for line in hunk.lines:
                    origin = line.origin  # '+', '-', or ' '
                    content = line.content.rstrip("\n")

                    if origin == "+":
                        lines.append(
                            {
                                "type": "added",
                                "lineno_old": None,
                                "lineno_new": new_lineno,
                                "content": content,
                            }
                        )
                        new_lineno += 1
                        added_lines += 1

                    elif origin == "-":
                        lines.append(
                            {
                                "type": "deleted",
                                "lineno_old": old_lineno,
                                "lineno_new": None,
                                "content": content,
                            }
                        )
                        old_lineno += 1
                        deleted_lines += 1

                    else:
                        lines.append(
                            {
                                "type": "context",
                                "lineno_old": old_lineno,
                                "lineno_new": new_lineno,
                                "content": content,
                            }
                        )
                        old_lineno += 1
                        new_lineno += 1

            changes.append(
                {
                    "old_file_path": delta.old_file.path,
                    "new_file_path": new_path,
                    "status": status,
                    "added_lines": added_lines,
                    "deleted_lines": deleted_lines,
                    "lines": lines,
                }
            )

        changes.sort(key=lambda c: c["new_file_path"] or c["old_file_path"])
        return changes

    def get_commit_diff_between_refs(self, source_ref: str, target_ref: str):
        """
        Returns a list of commits present in `source_ref` but not in `target_ref`,
        like `git log target_ref..source_ref`.
        """
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"{target_ref}..{source_ref}",
                    "--format=%H|%ct|%s|%an|%ae",
                ],
                cwd=self._local_git_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

            commits = []
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    commit_hash, timestamp, message, author_name, author_email = (
                        line.split("|", 4)
                    )
                    commits.append(
                        {
                            "hash": commit_hash,
                            "timestamp": datetime.fromtimestamp(int(timestamp)),
                            "message": message.strip(),
                            "author_name": author_name,
                            "author_email": author_email,
                        }
                    )
                except ValueError:
                    continue  # Skip malformed lines

            return commits

        except subprocess.CalledProcessError as e:
            print("Git commit diff error:", e.stderr)
            return []


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
