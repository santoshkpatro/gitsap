from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProjectPermission, Project


@receiver(post_save, sender=Project)
def assign_owner_permission(sender, instance: Project, created: bool, **kwargs):
    """
    Signal: Runs after a Project is created.
    Ensures the project creator (user/org) has the OWNER role.
    """
    if not created:
        return

    if instance.owner_type == "user":
        # For user-owned projects → the user becomes OWNER
        ProjectPermission.objects.create(
            user=instance.owner_user,
            project=instance,
            role=ProjectPermission.Role.OWNER,
        )
    elif instance.owner_type == "organization":
        # For org-owned projects → the creator is set as OWNER
        ProjectPermission.objects.create(
            user=instance.created_by,
            project=instance,
            role=ProjectPermission.Role.OWNER,
        )
