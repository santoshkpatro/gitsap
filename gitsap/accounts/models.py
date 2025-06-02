import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.text import slugify
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from zoneinfo import available_timezones

from gitsap.shared.models import BaseUUIDModel


class UserManager(BaseUserManager):
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(BaseUUIDModel, AbstractBaseUser):
    username = models.CharField(max_length=128, unique=True, blank=True)
    email = models.EmailField(max_length=128, unique=True)
    first_name = models.CharField(max_length=128, blank=True, null=True)
    last_name = models.CharField(max_length=128, blank=True, null=True)
    avatar = models.ForeignKey(
        "attachments.Attachment", on_delete=models.SET_NULL, null=True, blank=True
    )
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    company = models.CharField(max_length=128, blank=True, null=True)
    timezone = models.CharField(
        max_length=64,
        choices=[(tz, tz) for tz in sorted(available_timezones())],
        default="UTC",
    )

    activated_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.email}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.username = slugify(self.email.split("@")[0])
        return super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def avatar_url(self):
        email = self.email.strip().lower().encode("utf-8")
        email_hash = hashlib.md5(email).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s=64&d=retro"

    @property
    def is_active(self):
        return self.activated_at is not None

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split("@")[0]

    @property
    def verification_link(self):
        uid = urlsafe_base64_encode(force_bytes(self.id))
        token = default_token_generator.make_token(self)

        return f"{settings.BASE_URL}/{reverse("accounts-email-verification", args=[uid, token])}"
