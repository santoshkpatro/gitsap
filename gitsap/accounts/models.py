from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.exceptions import ValidationError

from gitsap.common.models import BaseCommonModel


class UserManager(BaseUserManager):
    def create_superuser(self, username, email_address, full_name, password):
        user = self.model(
            username=username,
            email_address=self.normalize_email(email_address),
            full_name=full_name,
        )
        user.set_password(password)
        user.is_superuser = True
        user.save()
        return user


class User(BaseCommonModel, AbstractBaseUser):
    username = models.CharField(max_length=128, unique=True)
    email_address = models.EmailField(unique=True)
    full_name = models.CharField(max_length=128)

    is_superuser = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email_address", "full_name"]
    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        db_table = "users"

    @classmethod
    def create_admin_user(cls, **user_details):
        password, _ = user_details.pop("password"), user_details.pop("confirm_password")
        admin_user = cls(
            **user_details,
        )
        admin_user.set_password(password)
        admin_user.is_superuser = True
        admin_user.save()

        return admin_user

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
