from django.apps import AppConfig


class GitsapConfig(AppConfig):
    name = 'gitsap'

    def ready(self):
        import gitsap.signals