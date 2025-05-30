from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gitsap.projects"

    def ready(self):
        import gitsap.projects.signals  # noqa
