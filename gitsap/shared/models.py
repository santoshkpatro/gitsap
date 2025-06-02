import uuid
from django.db import models
from django.apps import apps
from django.shortcuts import get_object_or_404


class BaseUUIDModel(models.Model):
    """
    Abstract base model that provides a UUID primary key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ATTACHMENT_FIELDS = []  # List of attachment-related field names

    class Meta:
        abstract = True

    def apply_updates(self, data: dict):
        """
        Update model fields from dict with attachment handling and minimal DB updates.
        """
        Attachment = apps.get_model(
            "attachments", "Attachment"
        )  # app_label, model_name

        updated = []

        for field, value in data.items():
            if field in self.ATTACHMENT_FIELDS:
                old_value = getattr(self, field, None)
                if old_value and old_value != value:
                    try:
                        get_object_or_404(Attachment, id=old_value).remove()
                    except Exception:
                        pass

                if value and value != old_value:
                    try:
                        get_object_or_404(Attachment, id=value).confirm()
                    except Exception:
                        pass

            if getattr(self, field, None) != value:
                setattr(self, field, value)
                updated.append(field)

        if updated:
            self.save(
                update_fields=updated + ["updated_at"]
            )  # always update updated_at
