from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gitsap.organizations"

    def ready(self):
        import gitsap.organizations.signals  # noqa
