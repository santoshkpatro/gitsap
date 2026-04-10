from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from gitsap.models.shared import BaseModel
from gitsap.models.choices import UserRoleChoice


class UserManager(BaseUserManager):
    def create_superuser(self, username, primary_email, full_name, password=None):
        user = self.model(
            username=username,
            primary_email=primary_email,
            full_name=full_name,
            role=UserRoleChoice.SUPERUSER
        )
        user.set_password(password)
        user.save()

        return user


class User(AbstractBaseUser, BaseModel):
    username = models.CharField(max_length=128, unique=True)
    primary_email = models.EmailField()
    full_name = models.CharField(max_length=128, blank=True, null=True)
    role = models.CharField(
        max_length=16, choices=UserRoleChoice.choices, default=UserRoleChoice.USER
    )
    deactivated_at = models.DateTimeField(blank=True, null=True)
    deactivate_note = models.CharField(max_length=128, blank=True, null=True)

    ID_PREFIX = "usr"
    REQUIRED_FIELDS = ["primary_email", "full_name"]
    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        db_table = "users"

    @property
    def is_active(self):
        return self.deactivated_at is not None

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.role == UserRoleChoice.SUPERUSER

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True    