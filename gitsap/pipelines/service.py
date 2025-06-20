import yaml
import docker
from gitsap.pipelines.models import PipelineJob
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class GitsapWorkflowParser:
    # Sample YAML structure for Gitsap workflow
    """
    steps:
        - build
        - test
        - deploy

    job-one-a:
        name: Build Job
        step: build
        commands:
            - echo "Building the project"
            - make build

    job-one-b:
        name: Another Build Job
        step: build
        commands:
            - echo "Running additional build steps"
            - make additional-build

    job-two:
        name: Test Job
        step: test
        commands:
            - echo "Running tests"
            - make test

    job-three:
        name: Deploy Job
        step: deploy
        commands:
            - echo "Deploying the project"
            - make deploy
    """

    def __init__(self, content):
        self.content = content
        self.data = {}

    def load(self):
        raw = yaml.safe_load(self.content)
        self.data["steps"] = raw.pop("steps", [])
        self.data["jobs"] = []
        self.data["image"] = raw.pop("image", "alpine:latest")

        for key, val in raw.items():
            job = {
                "key": key,
                "name": val.get("name", key),
                "step": val.get("step"),
                "image": val.get("image", self.data["image"]),
                "commands": val.get("commands", []),
            }
            self.data["jobs"].append(job)

        print("[parser] Parsed workflow data:", self.data)

        return self.data


class GitsapWorkflowRunner:
    def __init__(self, job_id):
        self._job = PipelineJob.objects.get(id=job_id)
        self._logs = []
        self._container_name = f"gitsap-job-{self._job.id.hex}"
        self._docker = docker.from_env()

    def relay_log(self, message):
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"job-{self._job.id}",
            {
                "type": "job_log_event",  # Matches the method name in consumer
                "message": message,
            },
        )

    def emit_log(self, message, source="job"):
        """
        Emit logs to the job's relay channel.
        This is a helper method to send logs directly.
        """

        timestamp = timezone.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{source}] {message}"

        self._logs.append(formatted)
        self.relay_log(formatted)

        if settings.DEBUG:
            print(formatted)

    def execute(self):
        try:
            self.emit_log(f"Starting job `{self._job.name}`", "job")

            self.emit_log(f"Pulling image `{self._job.image}`", "job")
            self._docker.images.pull(self._job.image)

            shell_command = " && ".join(self._job.commands)
            # self._logs.append(f"🧪 Running: `{shell_command}`")

            # Run container without auto-remove
            container = self._docker.containers.run(
                self._job.image,
                command=["sh", "-c", shell_command],
                name=self._container_name,
                detach=True,
                stdout=True,
                stderr=True,
                tty=False,  # You can enable this if needed
            )

            # Stream logs
            for line in container.logs(stream=True):
                log = line.decode().rstrip()
                if settings.DEBUG:
                    print(f"[container] {log}", "container")
                self.emit_log(log)

            # Wait for container to finish
            result = container.wait()  # Blocks until done
            exit_code = result.get("StatusCode", 1)

            self.emit_log(f"Container exited with code: {exit_code}", "job")

            # Cleanup container manually
            container.remove(force=True)

            if exit_code == 0:
                self.emit_log(f"Job `{self._job.name}` completed successfully.", "job")
                return True, "\n".join(self._logs)
            else:
                self.emit_log(
                    f"Job `{self._job.name}` failed with exit code {exit_code}."
                )
                return False, "\n".join(self._logs)

        except Exception as e:
            self.emit_log(f"🔥 Error during job execution: {str(e)}", "job")
            return False, "\n".join(self._logs)
