from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils import timezone
from django.urls import reverse
from django.conf import settings

from gitsap.base.models import BaseModel
from gitsap.users.managers import UserManager


class User(BaseModel, AbstractBaseUser):
    class Role(models.TextChoices):
        BASIC = ("basic", "Basic")
        ADMIN = ("admin", "Admin")

    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BASIC)
    avatar = models.ImageField(upload_to="user/avatars/", null=True, blank=True)

    timezone = models.CharField(max_length=64, default="UTC")
    locale = models.CharField(max_length=10, default="en")

    # Status fields
    activated_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)

    # Security fields
    password_changed_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # Audit fields
    last_login = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # 2FA fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "full_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"

    @property
    def verification_link(self):
        """
        Generates a unique activation link with uid + token.
        Example usage in email: user.activation_link
        """

        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        path = reverse(
            "users-verification-confirm", kwargs={"uidb64": uid, "token": token}
        )
        return "{}{}".format(settings.BASE_URL, path)

    @property
    def resend_verification_link(self):
        """
        Generates a unique link to resend the activation email with uid.
        Example usage in email: user.resend_verification_link
        """

        uid = urlsafe_base64_encode(force_bytes(self.pk))
        path = reverse("users-verification-resend", kwargs={"uidb64": uid})
        return "{}{}".format(settings.BASE_URL, path)

    def verify(self, token):
        """
        Validate the token and activate the user.
        Returns True if successful, False otherwise.
        """

        uid = urlsafe_base64_encode(force_bytes(self.pk))
        if default_token_generator.check_token(self, token):
            if not self.verified_at:
                self.verified_at = timezone.now()
            self.save(update_fields=["verified_at"])
            return True

        return False

    def revoke_verification(self):
        if self.verified_at:
            self.verified_at = None
            self.save(update_fields=["verified_at"])
