import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


LAYOUTS = {
    "project": "layouts/project_layout.html",
    "app": "layouts/app_layout.html",
}

TEMPLATE_CONTENT = """\
{{% extends '{layout}' %}}

{{% block styles_content %}}
{{% endblock styles_content %}}

{{% block top_bar_content %}}
{{% endblock top_bar_content %}}

{{% block main_content %}}
{{% endblock main_content %}}

{{% block footer_content %}}
{{% endblock footer_content %}}

{{% block scripts_content %}}
{{% endblock scripts_content %}}
"""


class Command(BaseCommand):
    help = "Dev utility: scaffold a new template with block stubs for a given layout"

    def add_arguments(self, parser):
        parser.add_argument(
            "template_path",
            help="Relative path for the new template inside the templates directory (e.g. projects/new_page.html)",
        )
        parser.add_argument(
            "--layout",
            choices=list(LAYOUTS.keys()),
            help="Layout to extend. Choices: %(choices)s",
        )

    def handle(self, *args, **options):
        template_path = options["template_path"]
        layout_key = options.get("layout")

        if not layout_key:
            self.stdout.write("Available layouts:")
            for i, key in enumerate(LAYOUTS, 1):
                self.stdout.write(f"  [{i}] {key}  →  {LAYOUTS[key]}")
            self.stdout.write("")

            choice = input("Pick a layout (name or number): ").strip()
            keys = list(LAYOUTS.keys())

            if choice.isdigit():
                idx = int(choice) - 1
                if idx < 0 or idx >= len(keys):
                    raise CommandError(f"Invalid choice: {choice}")
                layout_key = keys[idx]
            elif choice in LAYOUTS:
                layout_key = choice
            else:
                raise CommandError(
                    f"Unknown layout '{choice}'. Valid options: {', '.join(LAYOUTS)}"
                )

        layout_file = LAYOUTS[layout_key]
        content = TEMPLATE_CONTENT.format(layout=layout_file)

        # Resolve destination path relative to the app's templates dir
        app_dir = Path(__file__).resolve().parents[3]  # gitsap/
        templates_dir = app_dir / "gitsap" / "templates"
        dest = templates_dir / template_path

        if dest.exists():
            raise CommandError(f"Template already exists: {dest}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)

        self.stdout.write(
            self.style.SUCCESS(f"Created template: {dest.relative_to(app_dir)}")
        )
        self.stdout.write(f"  extends: {layout_file}")
