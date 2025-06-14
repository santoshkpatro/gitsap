import yaml


class GitsapWorkflowParser:
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
