from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, email, full_name, password=None):
        if not username:
            raise ValueError('The Username field is required')
        if not email:
            raise ValueError('The Email field is required')
        if not full_name:
            raise ValueError('The Full Name field is required')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, full_name=full_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, full_name, password=None):
        user = self.create_user(username, email, full_name, password)
        user.is_admin = True
        user.save(using=self._db)
        return user