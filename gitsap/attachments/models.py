from django.db import models
from django.utils import timezone

from gitsap.shared.models import BaseUUIDModel


class Attachment(BaseUUIDModel):
    file = models.FileField(upload_to="attachments/%Y/%m/%d/")
    deleted_at = models.DateTimeField(blank=True, null=True)

    # Metadata
    filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    checksum = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "attachments"

    def __str__(self):
        return f"Attachment {self.id} - {self.filename or self.file.name}"

    def remove(self):
        """Mark the attachment as deleted."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    @property
    def url(self):
        """Return the URL of the attachment file."""
        if self.deleted_at:
            return None
        return self.file.url if self.file else None

    @property
    def key(self):
        """Return the key for the attachment file."""
        return self.file.name if self.file else None
