from django.db import models

from gitsap.base.models import BaseModel


# class Commit(BaseModel):
#     project = models.ForeignKey(
#         "Project", on_delete=models.CASCADE, related_name="commits"
#     )
#     sha = models.CharField(max_length=40, unique=True)
#     message = models.TextField()
#     author_name = models.CharField(max_length=100)
#     author_email = models.EmailField()
#     committed_at = models.DateTimeField()

#     class Meta:
#         db_table = "commits"
#         ordering = ["-committed_at"]


# class CommitFile(BaseModel):
#     class ChangeType(models.TextChoices):
#         ADDED = ("A", "Added")
#         MODIFIED = ("M", "Modified")
#         DELETED = ("D", "Deleted")
#         RENAMED = ("R", "Renamed")

#     commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name="files")
#     file_path = models.TextField()
#     change_type = models.CharField(max_length=1, choices=ChangeType.choices)

#     class Meta:
#         db_table = "commit_files"
#         ordering = ["filename"]
