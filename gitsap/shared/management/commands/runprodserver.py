import os
import subprocess
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Starts the production Uvicorn server. PORT can be set via env (default: 8000)."
    )

    def handle(self, *args, **options):
        port = os.environ.get("PORT", "8000")

        command = ["uvicorn", "config.asgi:application", "--port", str(port)]

        self.stdout.write(f"Running production server on port {port}...")
        subprocess.run(command)
