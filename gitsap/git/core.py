import pygit2
import mimetypes
from django.utils import timezone
import datetime

TYPE_MAP = {
    pygit2.GIT_OBJECT_TREE: "tree",
    pygit2.GIT_OBJECT_BLOB: "blob",
    pygit2.GIT_OBJECT_COMMIT: "commit",
    pygit2.GIT_OBJECT_TAG: "tag",
}

FILE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",  # CodeMirror treats TS as JS w/ types
    ".html": "htmlmixed",
    ".htm": "htmlmixed",
    ".css": "css",
    ".scss": "css",
    ".json": "javascript",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".md": "markdown",
    ".txt": "null",  # plain text (no highlighting)
    ".xml": "xml",
    ".java": "clike",
    ".c": "clike",
    ".cpp": "clike",
    ".h": "clike",
    ".go": "go",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
}


class GitService:
    def __init__(self, repo_path):
        self._repo = pygit2.Repository(repo_path)

    def list_branches(self):
        return list(self._repo.branches.local)

    def _last_commits_for_paths(self, branch_name, paths):
        """
        Walk branch history once and return {path: last_commit}.
        """
        reference = self._repo.branches[branch_name]
        head_commit = reference.peel(pygit2.Commit)

        # prepare lookup
        remaining = set(paths)
        results = {p: None for p in paths}

        walker = self._repo.walk(head_commit.id, pygit2.GIT_SORT_TIME)
        walker.simplify_first_parent()  # follow mainline

        for commit in walker:
            if not remaining:
                break
            for parent in commit.parents:
                diff = self._repo.diff(parent, commit)
                for patch in diff:
                    path = patch.delta.new_file.path
                    if path in remaining:
                        results[path] = commit
                        remaining.remove(path)

        # fallback: if never changed after HEAD, assign head commit
        for path in remaining:
            results[path] = head_commit
        return results

    def list_tree(self, branch_name, path=None):
        """
        List objects at the given branch and path.
        If path=None -> root tree.
        If path="src/utils" -> tree inside src/utils.
        """
        reference = self._repo.branches[branch_name]
        commit = reference.peel(pygit2.Commit)

        # Start at root tree
        tree = commit.tree
        if path:
            for part in path.strip("/").split("/"):
                entry = tree[part]
                if entry.type != pygit2.GIT_OBJECT_TREE:
                    raise ValueError(
                        f"'{path}' is not a directory in branch '{branch_name}'"
                    )
                tree = self._repo[entry.id]

        # Collect entries
        entries = list(tree)
        full_paths = [(path + "/" if path else "") + entry.name for entry in entries]

        # Get last commits in one pass
        last_commits = self._last_commits_for_paths(branch_name, full_paths)

        objects = []
        for entry, full_path in zip(entries, full_paths):
            obj = self._repo[entry.id]
            last_commit = last_commits[full_path]

            # detect file extension and map to mode
            ext = "." + entry.name.split(".")[-1] if "." in entry.name else ""
            file_type = FILE_MAP.get(ext.lower(), "null")

            commit_time = timezone.localtime(
                datetime.datetime.fromtimestamp(
                    last_commit.commit_time, tz=datetime.timezone.utc
                )
            )
            objects.append(
                {
                    "name": entry.name,
                    "type": TYPE_MAP.get(entry.type, entry.type),
                    "id": str(entry.id),
                    "size": obj.size if entry.type == pygit2.GIT_OBJECT_BLOB else None,
                    "file_type": (
                        file_type if entry.type == pygit2.GIT_OBJECT_BLOB else None
                    ),
                    "nodepath": full_path,
                    "last_commit": {
                        "id": str(last_commit.id),
                        "message": last_commit.message.strip(),
                        "author": {
                            "name": last_commit.author.name,
                            "email": last_commit.author.email,
                        },
                        "time": commit_time,
                    },
                }
            )

        # Sort: directories first, then files; both alphabetically
        objects.sort(key=lambda o: (0 if o["type"] == "tree" else 1, o["name"].lower()))
        return objects

    def get_blob_content(self, branch_name, path):
        """
        Return blob content at given branch/path.
        """
        reference = self._repo.branches[branch_name]
        commit = reference.peel(pygit2.Commit)

        tree = commit.tree
        for part in path.strip("/").split("/"):
            entry = tree[part]
            if entry.type == pygit2.GIT_OBJECT_TREE:
                tree = self._repo[entry.id]
            elif entry.type == pygit2.GIT_OBJECT_BLOB:
                blob = self._repo[entry.id]
                # Return decoded text if not binary
                if blob.is_binary:
                    return None
                return blob.data.decode("utf-8", errors="replace")
        return None
