import uuid
from django.db import models


class BaseUUIDTimestampModel(models.Model):
    """
    Abstract base model that includes a UUID primary key and timestamp fields.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
