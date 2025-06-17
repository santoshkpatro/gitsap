"""
ASGI config for gitsap project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# from django.core.asgi import get_asgi_application
from gitsap.relay_urls import urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gitsap.settings")
django.setup()

application = ProtocolTypeRouter(
    {"websocket": AuthMiddlewareStack(URLRouter(urlpatterns))}
)
