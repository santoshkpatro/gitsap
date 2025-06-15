from celery import shared_task
from django.db import transaction
from gitsap.projects.models import Project
from gitsap.pipelines.service import GitsapWorkflowParser
from gitsap.pipelines.models import Pipeline, PipelineStep, PipelineJob


@shared_task
def dispatch_gitsap_pipeline(project_id, user_id, ref):
    project = Project.objects.filter(id=project_id).first()
    if not project:
        print(f"Project with ID {project_id} not found.")
        return

    git_service = project.git_service
    last_commit = git_service.get_last_commit_info_for_ref(ref)
    content = git_service.get_workflow_content(last_commit["hash"])

    if not content:
        return

    parser = GitsapWorkflowParser(content)
    workflow_data = parser.load()

    print("Parsed workflow data:", workflow_data)

    try:
        with transaction.atomic():
            pipeline = Pipeline.objects.create(
                project=project,
                name=last_commit["message"],
                source=Pipeline.Source.PUSH,
                commit_sha=last_commit["hash"],
                triggered_by_id=user_id,
            )
            for index, step_name in enumerate(workflow_data.get("steps", [])):
                pipeline_step = PipelineStep.objects.create(
                    pipeline=pipeline,
                    name=step_name,
                    sequence=index + 1,
                )
                for job_data in workflow_data.get("jobs", []):
                    if job_data.get("step") == step_name:
                        PipelineJob.objects.create(
                            pipeline=pipeline,
                            step=pipeline_step,
                            name=job_data.get("name", ""),
                            image=job_data.get("image", pipeline.default_image),
                            commands=job_data.get("commands", []),
                            only=job_data.get("only", []),
                        )
    except Exception as e:
        print(f"Error creating pipeline for project {project_id} and ref {ref}: {e}")
        return
