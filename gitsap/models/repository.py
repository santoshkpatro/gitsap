import pygit2
import os
from django.db import models

from gitsap.models.shared import BaseTimestampModel


class Repository(BaseTimestampModel):
    project = models.OneToOneField(
        "Project",
        primary_key=True,
        related_name="repository",
        on_delete=models.CASCADE,
    )
    repo_path = models.CharField(max_length=512, unique=True, blank=True)
    is_empty = models.BooleanField(default=True)

    class Meta:
        db_table = "repositories"

    @classmethod
    def init_bare_repo_path(cls, repo_path):
        os.makedirs(os.path.dirname(repo_path), exist_ok=True)
        repo = pygit2.init_repository(repo_path, bare=True)
        return repo

    @property
    def repo(self):
        return pygit2.Repository(self.repo_path)
    
    @property
    def branches(self):
        # TODO: Can perform redis caching for better perf
        return self.list_branches(branch_type="local")

    def list_branches(self, branch_type="local"):
        if branch_type == "local":
            return [b for b in self.repo.branches.local]
        elif branch_type == "remote":
            return [b for b in self.repo.branches.remote]
        else:
            raise ValueError("branch_type must be 'local' or 'remote'")

    