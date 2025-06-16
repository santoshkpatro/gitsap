import yaml
import docker
from gitsap.pipelines.models import PipelineJob


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
            - run: echo "Building the project"
            - run: make build

    job-one-b:
        name: Another Build Job
        step: build
        commands:
            - run: echo "Running additional build steps"
            - run: make additional-build

    job-two:
        name: Test Job
        step: test
        commands:
            - run: echo "Running tests"
            - run: make test

    job-three:
        name: Deploy Job
        step: deploy
        commands:
            - run: echo "Deploying the project"
            - run: make deploy

    """

    def __init__(self, content):
        self.content = content
        self.data = {}

    def load(self):
        raw = yaml.safe_load(self.content)

        self.data["steps"] = raw.get("steps", [])

        self.data["jobs"] = []
        for key, val in raw.items():
            if key == "steps":
                continue  # skip the 'steps' key

            # Defensive check: job must be a dict with at least 'commands'
            if not isinstance(val, dict) or "commands" not in val:
                continue

            job = {
                "key": key,
                "name": val.get("name", key),
                "step": val.get("step"),
                "commands": [cmd["run"] for cmd in val.get("commands", [])],
            }
            self.data["jobs"].append(job)

        return self.data


class GitsapWorkflowRunner:
    def __init__(self, job_id):
        self._job = PipelineJob.objects.get(id=job_id)
        self._logs = []
        self._container_name = f"gitsap-job-{self._job.id.hex[:8]}"
        self._docker = docker.from_env()

    def execute(self):
        try:
            self._logs.append(f"🏁 Starting job `{self._job.name}`")

            self._logs.append(f"📦 Pulling image: `{self._job.image}`")
            self._docker.images.pull(self._job.image)

            shell_command = " && ".join(self._job.commands)
            self._logs.append(f"🧪 Running: `{shell_command}`")

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
                self._logs.append(line.decode().rstrip())

            # Wait for container to finish
            result = container.wait()  # Blocks until done
            exit_code = result.get("StatusCode", 1)

            self._logs.append(f"🚪 Exit code: {exit_code}")

            # Cleanup container manually
            container.remove(force=True)

            if exit_code == 0:
                self._logs.append(f"✅ Job `{self._job.name}` completed successfully.")
                return True, "\n".join(self._logs)
            else:
                self._logs.append(f"❌ Job `{self._job.name}` failed.")
                return False, "\n".join(self._logs)

        except Exception as e:
            self._logs.append(f"🔥 Error during job: {str(e)}")
            return False, "\n".join(self._logs)
