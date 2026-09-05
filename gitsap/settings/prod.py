import dj_database_url
import os
from gitsap.settings.base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(",")

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("PG_PROD_URL")
    )
}