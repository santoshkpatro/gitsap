import uuid
from django.conf import settings


class RequestIDMiddleware:
    """
    Adds X-Request-Id to non-static/media requests.
    """
    header_name = "X-Request-Id"

    def __init__(self, get_response):
        self.get_response = get_response
        # Build a small skip list once
        self._skip_prefixes = []
        static_url = getattr(settings, "STATIC_URL", None)
        media_url  = getattr(settings, "MEDIA_URL", None)
        if static_url:
            self._skip_prefixes.append(static_url)
        if media_url:
            self._skip_prefixes.append(media_url)
        # Common asset paths to exclude as well
        self._skip_prefixes += ["/favicon.ico", "/robots.txt"]

    def _should_skip(self, path):
        return any(path.startswith(p) for p in self._skip_prefixes)

    def __call__(self, request):
        # Don’t attach for static/media (or other skipped) paths
        if self._should_skip(request.path):
            return self.get_response(request)

        rid = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.request_id = rid  # available to views/handlers
        response = self.get_response(request)
        response[self.header_name] = rid
        return response
