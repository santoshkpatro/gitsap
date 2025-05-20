from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from gitsap.pull_requests.models import PullRequest


@receiver(post_save, sender=PullRequest)
def increment_pull_request_count(sender, instance, created, **kwargs):
    if created:
        # Increment the pull request count for the associated project
        project = instance.project
        project.total_pull_requests_count += 1
        if instance.status == PullRequest.Status.OPEN:
            project.open_pull_requests_count += 1
        project.save(
            update_fields=["total_pull_requests_count", "open_pull_requests_count"]
        )


@receiver(post_delete, sender=PullRequest)
def decrement_pull_request_count(sender, instance, **kwargs):
    # Decrement the pull request count for the associated project
    project = instance.project
    project.total_pull_requests_count -= 1

    if instance.status == PullRequest.Status.OPEN:
        project.open_pull_requests_count -= 1
    elif instance.status == PullRequest.Status.MERGED:
        project.merged_pull_requests_count -= 1
    project.save(
        update_fields=[
            "total_pull_requests_count",
            "open_pull_requests_count",
            "merged_pull_requests_count",
        ]
    )
