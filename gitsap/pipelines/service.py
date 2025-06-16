import yaml
import time
import random
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

    def execute(self):
        try:
            self._logs.append(f"Starting job {self._job.name} (ID: {self._job.id})")
            for command in self._job.commands:
                self._logs.append(f"Executing command: {command}")
                # Simulate command execution with a random delay
                time.sleep(random.randint(10, 22))
                # Here you would normally execute the command, e.g., using subprocess
            self._logs.append(f"Job {self._job.name} completed successfully.")
            return True, "\n".join(self._logs)
        except Exception as e:
            self._logs.append(f"Job {self._job.name} failed with error: {str(e)}")
            return False, "\n".join(self._logs)
