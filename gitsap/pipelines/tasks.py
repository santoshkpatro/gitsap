from celery import shared_task, group, chord
from gitsap.pipelines.models import Pipeline, PipelineStep, PipelineJob
from gitsap.pipelines.service import GitsapWorkflowRunner
from django.utils import timezone


@shared_task
def run_job(job_id):
    job = PipelineJob.objects.filter(id=job_id).first()
    if not job:
        return False

    job.status = PipelineJob.Status.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    runner = GitsapWorkflowRunner(job.id)
    ok, logs = runner.execute()
    job.log_content = logs

    if ok:
        job.status = PipelineJob.Status.SUCCESS
        print(f"✅ Job {job.id} completed successfully.")
    else:
        job.status = PipelineJob.Status.FAILED
        print(f"❌ Job {job.id} failed.")

    job.finished_at = timezone.now()
    job.save(update_fields=["status", "log_content", "finished_at"])

    if job.ignore_failure:
        print(f"⚠️ Job {job.id} ignored failure due to ignore_failure flag.")
        return True

    return ok


@shared_task
def on_step_complete(results, step_id):
    """
    Called after all jobs in a step complete.
    """
    if not all(results):
        print(f"❌ Step {step_id} failed. Stopping pipeline.")
        step = PipelineStep.objects.filter(id=step_id).first()
        if step:
            step.pipeline.status = Pipeline.Status.FAILED
            step.pipeline.save()
        return

    # Move to next step
    current_step = (
        PipelineStep.objects.select_related("pipeline").filter(id=step_id).first()
    )
    if not current_step:
        return

    next_step = current_step.pipeline.steps.filter(
        sequence=current_step.sequence + 1
    ).first()
    if next_step:
        run_step.delay(next_step.id)
    else:
        # If no next step, mark pipeline as complete
        current_step.pipeline.status = Pipeline.Status.SUCCESS
        current_step.pipeline.save()
        print(f"✅ Pipeline {current_step.pipeline.id} completed.")


@shared_task
def run_step(step_id):
    """
    Runs all jobs of a step in parallel, moves to next step via callback.
    """
    step = PipelineStep.objects.prefetch_related("jobs").filter(id=step_id).first()
    if not step:
        return

    job_group = group(run_job.si(job.id) for job in step.jobs.all())
    callback = on_step_complete.s(step.id)
    chord(job_group)(callback)


@shared_task
def run_pipeline(pipeline_id):
    """
    Kicks off the pipeline from the first step.
    """
    pipeline = (
        Pipeline.objects.prefetch_related("steps__jobs").filter(id=pipeline_id).first()
    )
    if not pipeline:
        return

    first_step = pipeline.steps.order_by("sequence").first()
    if first_step:
        run_step.delay(first_step.id)
