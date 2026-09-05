import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Experimental Git receive-pack"

    def handle(self, *args, **options):
        stdin = sys.stdin.buffer

        while True:
            data = stdin.read(8192)

            if not data:
                break

            print(f"received {len(data)} bytes", file=sys.stderr)
