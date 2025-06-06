from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from gitsap.organizations.models import Organization, OrganizationUser


@receiver(post_save, sender=Organization)
def create_organization_owner(sender, instance, created, **kwargs):
    if created:
        # Automatically add the creator as the owner of the organization
        OrganizationUser.objects.create(
            organization=instance,
            user=instance.created_by,
            role=OrganizationUser.Role.OWNER,
        )
