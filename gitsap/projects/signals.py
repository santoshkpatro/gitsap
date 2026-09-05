from django.db.models.signals import post_save
from django.dispatch import receiver

from gitsap.projects.models import Project, ProjectMembershipRole, ProjectMembership


@receiver(post_save, sender=Project)
def create_owner_membership(sender, instance, created, **kwargs):
    if not created:
        return

    ProjectMembership.objects.create(
        project=instance, user=instance.owner, role=ProjectMembershipRole.OWNER
    )
