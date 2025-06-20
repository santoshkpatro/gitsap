from celery import shared_task
from django.db import transaction
from django.conf import settings
from gitsap.projects.models import Project
from gitsap.pipelines.service import GitsapWorkflowParser
from gitsap.pipelines.models import Pipeline, PipelineStep, PipelineJob
from gitsap.pipelines.tasks import run_pipeline


@shared_task
def dispatch_gitsap_pipeline(project_id, user_id, ref):
    project = Project.objects.filter(id=project_id).first()
    if not project:
        return

    git_service = project.git_service
    last_commit = git_service.get_last_commit_info_for_ref(ref)
    content = git_service.get_workflow_content(last_commit["hash"])

    if not content:
        return

    try:
        parser = GitsapWorkflowParser(content)
        workflow_data = parser.load()
        print("[worker] Parsed workflow data:", workflow_data)
    except Exception as e:
        print(
            f"[worker] Error parsing workflow for project {project_id} and ref {ref}: {e}"
        )
        return

    try:
        with transaction.atomic():
            pipeline = Pipeline.objects.create(
                project=project,
                name=last_commit["message"],
                source=Pipeline.Source.PUSH,
                commit_sha=last_commit["hash"],
                triggered_by_id=user_id,
                ref=ref,
                default_image=workflow_data.get("image", "alpine:latest"),
            )
            for index, step_name in enumerate(workflow_data.get("steps", [])):
                pipeline_step = PipelineStep.objects.create(
                    pipeline=pipeline,
                    name=step_name,
                    sequence=index + 1,
                )
                for job_data in workflow_data.get("jobs", []):
                    print("[worker] Processing job data:", job_data)
                    if job_data.get("step") == step_name:
                        PipelineJob.objects.create(
                            pipeline=pipeline,
                            step=pipeline_step,
                            name=job_data.get("name", ""),
                            image=job_data.get("image"),
                            commands=job_data.get("commands", []),
                            only=job_data.get("only", []),
                        )
    except Exception as e:
        print(
            f"[worker] Error creating pipeline for project {project_id} and ref {ref}: {e}"
        )
        return

    # Trigger the pipeline execution
    run_pipeline.delay(pipeline.id)
