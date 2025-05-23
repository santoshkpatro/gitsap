from django.apps import AppConfig


class PullRequestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gitsap.pull_requests"

    def ready(self):
        import gitsap.pull_requests.signals  # noqa
