from config.settings.base import *

# PRODUCTION Related Overrides

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
