from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gitsap.users"

    def ready(self):
        import gitsap.users.signals