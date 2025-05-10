from django.db.models.signals import post_save
from django.dispatch import receiver

from issues.models import Issue


@receiver(post_save, sender=Issue)
def increment_issue_count(sender, instance, created, **kwargs):
    if created:
        # Increment the issue count for the associated project
        project = instance.project
        project.total_issues_count += 1
        project.open_issues_count += 1
        project.save(update_fields=["total_issues_count", "open_issues_count"])
