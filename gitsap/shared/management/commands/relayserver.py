import subprocess
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Starts the ASGI relay server using Daphne"

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            type=str,
            default="127.0.0.1",
            help="Host to bind Daphne to (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8001,
            help="Port to bind Daphne to (default: 8001)",
        )

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]

        self.stdout.write(
            self.style.NOTICE(
                f"🚀 Starting Daphne relay server at http://{host}:{port} ..."
            )
        )

        try:
            subprocess.run(
                [
                    "daphne",
                    f"--bind={host}",
                    f"--port={port}",
                    "gitsap.asgi:application",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to start Daphne: {e}"))
