from gitsap.config.models import Config


def config(request):
    return {
        "config": Config.cached_instance(),
    }
