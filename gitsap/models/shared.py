from django.db import models

from gitsap.utils.generator import generate_ulid


class BaseModel(models.Model):
    id = models.CharField(max_length=40, editable=False, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ID_PREFIX = None

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.ID_PREFIX:
                raise ValueError(f"{self.__class__.__name__} must define ID_PREFIX")

            if not self.id:
                ulid = str(generate_ulid()).lower()
                prefix = self.ID_PREFIX.lower()
                self.id = f"{prefix}_{ulid}"

        return super().save(*args, **kwargs)

    def __str__(self):
        model_name = self.__class__.__name__

        # pk can be None before save
        pk = getattr(self, "pk", None)

        return f"{model_name}({pk if pk else 'NA'})"


class BaseTimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
