import pygit2


class GitService:
    def __init__(self, repo_path):
        self._repo = pygit2.Repository(repo_path)

    def list_branches(self):
        return list(self._repo.branches.local)
