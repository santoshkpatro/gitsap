import dj_database_url
import os
from gitsap.settings.base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {"default": dj_database_url.config(default=os.environ.get("PG_DEV_URL"))}
