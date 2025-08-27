from django.db import models
from django.contrib.auth.models import AbstractBaseUser

from gitsap.users.managers import UserManager


class User(AbstractBaseUser):
    class Role(models.TextChoices):
        BASIC = ("basic", "Basic")
        ADMIN = ("admin", "Admin")
    
    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BASIC)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'