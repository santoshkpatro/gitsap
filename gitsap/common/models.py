import uuid
from django.db import models


class BaseCommonModel(models.Model):
    id = models.UUIDField(default=uuid.uuid7, primary_key=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
