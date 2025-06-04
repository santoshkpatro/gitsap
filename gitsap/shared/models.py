import uuid
from django.db import models, transaction
from django.apps import apps


class BaseUUIDModel(models.Model):
    """
    Abstract base model with UUID primary key and update helper.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fields that are attachments and require special handling
    ATTACHMENT_FIELDS = []

    class Meta:
        abstract = True

    def apply_updates(self, data: dict):
        """
        Update model fields from a dict.
        Expects actual Attachment objects for ATTACHMENT_FIELDS.

        Returns:
            (changed: bool, errors: list)
        """
        updated_fields = []
        errors = []

        try:
            with transaction.atomic():
                for field, new_value in data.items():
                    if not hasattr(self, field):
                        continue  # Skip unknown fields

                    old_value = getattr(self, field)

                    if field in self.ATTACHMENT_FIELDS:
                        if old_value != new_value:
                            # Remove old attachment if it exists
                            if old_value:
                                try:
                                    old_value.remove()
                                except Exception as e:
                                    errors.append(
                                        f"{field}: failed to remove old attachment: {e}"
                                    )

                            # Confirm new attachment if provided
                            if new_value:
                                try:
                                    new_value.confirm()
                                except Exception as e:
                                    errors.append(
                                        f"{field}: failed to confirm new attachment: {e}"
                                    )

                            setattr(self, field, new_value)
                            updated_fields.append(field)
                    else:
                        if old_value != new_value:
                            setattr(self, field, new_value)
                            updated_fields.append(field)

                if updated_fields:
                    self.save(update_fields=updated_fields + ["updated_at"])

        except Exception as e:
            errors.append(str(e))
            return False, errors

        return bool(updated_fields), errors
