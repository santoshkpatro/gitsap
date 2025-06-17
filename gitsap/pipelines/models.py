from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.timesince import timesince

from gitsap.shared.models import BaseUUIDModel

STEP_STATUS_ICON_MAP = {
    "success": ("check-circle", "text-success"),
    "failed": ("x-circle", "text-danger"),
    "cancelled": ("ban", "text-secondary"),
    "in_progress": ("circle-dot-dashe", "text-primary"),
    "running": ("circle-dot-dashed", "text-primary"),
    "queued": ("clock", "text-muted"),
    "pending": ("clock", "text-muted"),
    "not_started": ("clock", "text-muted"),
    "default": ("help-circle", "text-muted"),
}

JOB_STATUS_ICON_MAP = {
    "queued": ("clock", "text-muted"),
    "pending": ("clock", "text-muted"),
    "running": ("circle-dot-dashed", "text-primary"),
    "success": ("circle-check", "text-success"),
    "failed": ("x-circle", "text-danger"),
    "cancelled": ("ban", "text-secondary"),
    "default": ("help-circle", "text-muted"),
}


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
    )
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
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

    @property
    def status(self):
        job_statuses = [job.status for job in self.jobs.all()]

        if not job_statuses:
            return "not_started"

        if all(s == PipelineJob.Status.PENDING for s in job_statuses):
            return "not_started"

        if any(s == PipelineJob.Status.FAILED for s in job_statuses):
            return "failed"

        if any(s == PipelineJob.Status.CANCELLED for s in job_statuses):
            return "cancelled"

        if all(s == PipelineJob.Status.SUCCESS for s in job_statuses):
            return "success"

        if any(
            s in [PipelineJob.Status.RUNNING, PipelineJob.Status.QUEUED]
            for s in job_statuses
        ):
            return "in_progress"

        return "in_progress"

    @property
    def icon_name(self):
        return STEP_STATUS_ICON_MAP.get(self.status, STEP_STATUS_ICON_MAP["default"])[0]

    @property
    def icon_class(self):
        return STEP_STATUS_ICON_MAP.get(self.status, STEP_STATUS_ICON_MAP["default"])[1]


class PipelineJob(BaseUUIDModel):
    class Status(models.TextChoices):
        QUEUED = ("queued", "Queued")
        PENDING = ("pending", "Pending")
        RUNNING = ("running", "Running")
        SUCCESS = ("success", "Success")
        FAILED = ("failed", "Failed")
        CANCELLED = ("cancelled", "Cancelled")

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
    log_content = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
    )
    ignore_failure = models.BooleanField(default=False)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "pipeline_jobs"
        verbose_name = "Pipeline Job"
        verbose_name_plural = "Pipeline Jobs"

    def __str__(self):
        return f"Pipeline Job -> {self.id}"

    @property
    def icon_name(self):
        return JOB_STATUS_ICON_MAP.get(self.status, JOB_STATUS_ICON_MAP["default"])[0]

    @property
    def icon_class(self):
        return JOB_STATUS_ICON_MAP.get(self.status, JOB_STATUS_ICON_MAP["default"])[1]

    @property
    def duration(self):
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    @property
    def duration_humanized(self):
        if not self.started_at or not self.finished_at:
            return None

        return timesince(
            self.started_at, self.finished_at
        )  # e.g., "3 minutes, 25 seconds"
