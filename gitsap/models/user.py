from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from zoneinfo import available_timezones

from gitsap.models.base import BaseUUIDTimestampModel

TIMEZONE_CHOICES = [(tz, tz) for tz in available_timezones()]


class UserManager(BaseUserManager):
    """
    Custom manager for User model.
    """

    def create_user(self, username, email, first_name, password=None, **extra_fields):
        """
        Create and return a user with an email and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(
            username=username, email=email, first_name=first_name, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username, email, first_name, password=None, **extra_fields
    ):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username, email, first_name, password, **extra_fields)

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class User(BaseUUIDTimestampModel, AbstractBaseUser):
    """
    User model to store user information.
    """

    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_password_expired = models.BooleanField(default=False)
    timezone = models.CharField(max_length=64, choices=TIMEZONE_CHOICES, default="UTC")

    first_name = models.CharField(max_length=128, blank=True, null=True)
    last_name = models.CharField(max_length=128, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(
        upload_to="users/avatars/%Y/%m/%d/", blank=True, null=True
    )
    deleted_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name"]

    objects = UserManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username

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
        return self.is_superuser
