from django.db import models
from django.contrib.postgres.fields import ArrayField

from gitsap.shared.models import BaseUUIDModel


class Pipeline(BaseUUIDModel):
    class Source(models.TextChoices):
        PUSH = ("push", "Push")
        PULL_REQUEST = ("pull_request", "Pull Request")
        SCHEDULED = ("scheduled", "Scheduled")

    class Status(models.TextChoices):
        QUEUED = ("queued", "Queued")
        PENDING = ("pending", "Pending")
        RUNNING = ("running", "Running")
        SUCCESS = ("success", "Success")
        FAILED = ("failed", "Failed")
        CANCELLED = ("cancelled", "Cancelled")

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="pipelines"
    )
    name = models.CharField(max_length=255, blank=False)
    source = models.CharField(max_length=32, choices=Source.choices)
    default_image = models.CharField(max_length=128, default="alpine:latest")
    commit_sha = models.CharField(max_length=128)
    ref = models.CharField(max_length=128)
    triggered_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="triggered_pipelines",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.QUEUED
    )

    class Meta:
        db_table = "pipelines"
        verbose_name = "Pipeline"
        verbose_name_plural = "Pipelines"

    def __str__(self):
        return f"Pipeline -> {self.name}"


class PipelineStep(BaseUUIDModel):
    pipeline = models.ForeignKey(
        "pipelines.Pipeline", on_delete=models.CASCADE, related_name="steps"
    )
    name = models.CharField(max_length=128)
    sequence = models.PositiveIntegerField()

    class Meta:
        db_table = "pipeline_steps"
        verbose_name = "Pipeline Step"
        verbose_name_plural = "Pipeline Steps"

    def __str__(self):
        return f"Pipeline Step -> {self.name} ({self.sequence})"


class PipelineJob(BaseUUIDModel):
    pipeline = models.ForeignKey(
        "pipelines.Pipeline", on_delete=models.CASCADE, related_name="jobs"
    )
    step = models.ForeignKey(
        "pipelines.PipelineStep", on_delete=models.CASCADE, related_name="jobs"
    )
    name = models.CharField(max_length=128)
    image = models.CharField(max_length=128, blank=True, null=True)
    commands = ArrayField(base_field=models.TextField(), default=list)
    only = ArrayField(base_field=models.CharField(max_length=128), default=list)

    class Meta:
        db_table = "pipeline_jobs"
        verbose_name = "Pipeline Job"
        verbose_name_plural = "Pipeline Jobs"

    def __str__(self):
        return f"Pipeline Job -> {self.id}"
