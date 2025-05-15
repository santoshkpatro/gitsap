import subprocess
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Starts Uvicorn with --reload using config.asgi:application."

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            type=str,
            default="127.0.0.1",
            help="Bind socket to this host. Default is 127.0.0.1",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Bind socket to this port. Default is 8000",
        )
        parser.add_argument(
            "--workers", type=int, help="Number of worker processes to use (optional)"
        )

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]
        workers = options.get("workers")

        command = [
            "uvicorn",
            "config.asgi:application",
            "--reload",
            "--host",
            host,
            "--port",
            str(port),
        ]

        if workers:
            command += ["--workers", str(workers)]

        self.stdout.write(f"Running: {' '.join(command)}")
        subprocess.run(command)
