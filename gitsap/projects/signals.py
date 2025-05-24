from django.db.models.signals import post_save
from django.dispatch import receiver

from gitsap.projects.models import Project, ProjectCollaborator


@receiver(post_save, sender=Project)
def initialize_git_repo_and_store(sender, instance, created, **kwargs):
    if created and not instance.resource:
        instance._setup_cloud_resource_artifact()


@receiver(post_save, sender=Project)
def add_owner_as_collaborator(sender, instance, created, **kwargs):
    if created:
        ProjectCollaborator.objects.create(
            project=instance, user=instance.created_by, role="owner"
        )
