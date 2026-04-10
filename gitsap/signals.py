import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from gitsap.models import Project, Repository


@receiver(post_save, sender=Project)
def create_repo(sender, instance, created, **kwargs):
    if created:
        repo_path = os.path.join(
            settings.GIT_REPO_BASE, f"{instance.namespace}.git"
        )

        Repository.init_bare_repo_path(repo_path)

        Repository.objects.create(
            project=instance,
            repo_path=repo_path,
        )
