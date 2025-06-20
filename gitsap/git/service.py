import os
import tempfile
import subprocess
import shutil
import difflib
from datetime import datetime
from pathlib import Path
import pygit2

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
    "html": "markup",
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


class GitService:
    def __init__(self, local_git_path: str):
        self.local_git_path = Path(local_git_path).resolve()
        self.repo = pygit2.Repository(str(self.local_git_path))

    def get_branches(self):
        return [
            ref.removeprefix("refs/heads/")
            for ref in self.repo.listall_references()
            if ref.startswith("refs/heads/")
        ]

    def get_tags(self):
        return [
            ref.removeprefix("refs/tags/")
            for ref in self.repo.listall_references()
            if ref.startswith("refs/tags/")
        ]

    def get_last_commit_info(self, relative_path, ref_name):
        try:
            ref = f"refs/heads/{ref_name}"
            cmd = ["git", "log", "-1", "--format=%H|%ct|%s|%an|%ae", ref]
            if relative_path:
                cmd += ["--", relative_path]

            result = subprocess.run(
                cmd,
                cwd=str(self.local_git_path),
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
        except subprocess.CalledProcessError:
            return None

    def get_blob_at_path(self, ref_name, relative_path):
        ref = self.repo.references.get(f"refs/heads/{ref_name}")
        if not ref:
            return None

        commit = self.repo[ref.target]
        tree = commit.tree

        parts = relative_path.strip("/").split("/")
        for part in parts[:-1]:
            try:
                tree_entry = tree[part]
                if tree_entry.type != pygit2.GIT_OBJECT_TREE:
                    return None
                tree = self.repo[tree_entry.id]
            except KeyError:
                return None

        try:
            blob_entry = tree[parts[-1]]
            if blob_entry.type != pygit2.GIT_OBJECT_BLOB:
                return None
            blob = self.repo[blob_entry.id]
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

    def get_commit_history(self, ref_name, max_count=50, skip=0):
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
                cwd=str(self.local_git_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
                    continue
            return history
        except subprocess.CalledProcessError:
            return []

    def get_diff_between_branches(self, source_branch, target_branch):
        try:
            source_commit = self.repo.revparse_single(f"refs/heads/{source_branch}")
            target_commit = self.repo.revparse_single(f"refs/heads/{target_branch}")
        except KeyError:
            return {"error": "One or both branches not found"}

        source_tree = source_commit.tree
        target_tree = target_commit.tree
        diff = self.repo.diff(target_tree, source_tree, context_lines=3)

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
                    origin = line.origin
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

    def get_conflict_lines(self, ours_oid, theirs_oid, ours_branch, theirs_branch):
        repo = self.repo
        ours_blob = repo[pygit2.Oid(hex=ours_oid)].data.decode("utf-8").splitlines()
        theirs_blob = repo[pygit2.Oid(hex=theirs_oid)].data.decode("utf-8").splitlines()

        # Use difflib for line-by-line comparison
        merged_lines = []
        sm = difflib.SequenceMatcher(None, ours_blob, theirs_blob)

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                merged_lines.extend(ours_blob[i1:i2])
            elif tag in ("replace", "delete", "insert"):
                merged_lines.append(f"<<<<<<< {ours_branch}")
                merged_lines.extend(ours_blob[i1:i2])
                merged_lines.append("=======")
                merged_lines.extend(theirs_blob[j1:j2])
                merged_lines.append(f">>>>>>> {theirs_branch}")

        return "\n".join(merged_lines)

    def get_merge_conflicts(self, source_branch: str, target_branch: str):
        bare_repo_path = self.local_git_path
        conflicts = []

        # Step 1: Check if branches are the same
        if source_branch == target_branch:
            return conflicts

        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone without checkout
            repo = pygit2.clone_repository(
                url=bare_repo_path, path=temp_dir, bare=False
            )

            try:
                source_ref = f"refs/remotes/origin/{source_branch}"
                target_ref = f"refs/remotes/origin/{target_branch}"
                source_commit = repo.revparse_single(source_ref)
                target_commit = repo.revparse_single(target_ref)
            except Exception as e:
                print("Error:", e)
                return []

            # Create local branches pointing to remote ones
            repo.create_branch(source_branch, source_commit)
            repo.create_branch(target_branch, target_commit)

            # Set HEAD and checkout target branch
            repo.set_head(f"refs/heads/{target_branch}")
            repo.checkout_tree(target_commit.tree, strategy=pygit2.GIT_CHECKOUT_FORCE)

            # Merge source into target
            repo.merge(source_commit.id)

            if repo.index.conflicts:
                for conflict in repo.index.conflicts:
                    ours = conflict[1]
                    theirs = conflict[2]
                    conflicts.append(
                        {
                            "path": (
                                ours.path if ours else (theirs.path if theirs else None)
                            ),
                            "ours": ours.hex if ours else None,
                            "theirs": theirs.hex if theirs else None,
                        }
                    )

            repo.state_cleanup()

        return conflicts

    def merge_branches(
        self,
        source_branch: str,
        target_branch: str,
        user_name: str,
        user_email: str,
        commit_message: str = None,
    ):
        """
        Clone the bare repo to a temp non-bare repo,
        perform a merge using pygit2, and push back if no conflicts.
        """

        bare_repo_path = self.local_git_path
        temp_dir = tempfile.mkdtemp()

        try:
            # Step 1: Clone from bare to temp non-bare repo
            repo = pygit2.clone_repository(
                url=f"file://{bare_repo_path}",
                path=temp_dir,
                bare=False,
                checkout_branch=target_branch,
            )

            # Step 2: Resolve the commits
            source_commit = repo.revparse_single(f"refs/remotes/origin/{source_branch}")
            target_commit = repo.revparse_single(f"refs/heads/{target_branch}")

            # Step 3: Checkout target branch
            repo.checkout(
                f"refs/heads/{target_branch}", strategy=pygit2.GIT_CHECKOUT_FORCE
            )
            repo.set_head(f"refs/heads/{target_branch}")

            # Step 4: Merge source into target
            repo.merge(source_commit.id)

            if repo.index.conflicts:
                # Abort merge if conflicts
                repo.state_cleanup()
                return {
                    "merged": False,
                    "conflicts": [
                        conflict[1].path
                        for conflict in repo.index.conflicts
                        if conflict[1]
                    ],
                }

            # Step 5: Write tree and create merge commit
            tree = repo.index.write_tree()
            author = pygit2.Signature(user_name, user_email)
            committer = pygit2.Signature(user_name, user_email)
            if not commit_message:
                commit_message = f"Merge branch '{source_branch}' into {target_branch}"
            merge_commit = repo.create_commit(
                f"refs/heads/{target_branch}",
                author,
                committer,
                commit_message,
                tree,
                [target_commit.id, source_commit.id],
            )

            # Step 6: Push back to origin
            remote = repo.remotes["origin"]
            remote.push(
                [f"refs/heads/{target_branch}"],
            )

            repo.state_cleanup()
            return {"merged": True, "merge_commit": str(merge_commit)}

        except Exception as e:
            return {"merged": False, "error": str(e)}

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

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
                cwd=self.local_git_path,
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

    def get_workflow_content(self, commit_sha):
        """
        Returns the content of `.gitsap-workflow.yaml` from the root of the given commit SHA.
        Returns None if the file is not found in the root.
        """
        try:
            commit = self.repo.revparse_single(commit_sha)
            if commit.type != pygit2.GIT_OBJECT_COMMIT:
                return None

            tree = commit.tree

            for entry in tree:
                if entry.name == ".gitsap-workflow.yaml":
                    blob = self.repo[entry.id]
                    return blob.data.decode("utf-8")

            return None  # Not found at root

        except (KeyError, ValueError, pygit2.GitError) as e:
            print(f"Error reading .gitsap-workflow.yaml: {e}")
            return None
