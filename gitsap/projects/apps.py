from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = "gitsap.projects"

    def ready(self):
        import gitsap.projects.signals