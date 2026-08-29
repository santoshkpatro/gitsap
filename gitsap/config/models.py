import tomllib
from django.db import models
from django.conf import settings
from django.core.cache import cache


class Config(models.Model):
    class BannerType(models.TextChoices):
        INFO = ("info", "Info")
        WARNING = ("warning", "Warning")
        ERROR = ("error", "Error")

    class SMTPEncryption(models.TextChoices):
        TLS = ("TLS", "TLS")
        SSL = ("SSL", "SSL")

    is_onboarded = models.BooleanField(default=False)
    organization_name = models.CharField(max_length=128)
    support_email_address = models.EmailField(max_length=128)
    application_url = models.URLField(blank=True, null=True)

    allow_login = models.BooleanField(default=True)
    allow_new_user = models.BooleanField(default=True)
    is_2fa_mandatory = models.BooleanField(default=False)

    maintaince_mode = models.BooleanField(default=False)
    maintaince_message = models.TextField(blank=True, null=True)

    banner_message = models.TextField(blank=True, null=True)
    banner_type = models.CharField(
        max_length=20, default=BannerType.INFO, choices=BannerType.choices
    )
    banner_expiry = models.DateTimeField(blank=True, null=True)

    smtp_email_host = models.CharField(max_length=128, blank=True, null=True)
    smtp_email_port = models.IntegerField(blank=True, null=True)
    smtp_host_user = models.CharField(max_length=128, blank=True, null=True)
    smtp_host_password = models.CharField(max_length=128, blank=True, null=True)
    smtp_encryption = models.CharField(
        max_length=8, blank=True, null=True, choices=SMTPEncryption.choices
    )
    smtp_default_from_email = models.EmailField(max_length=128, blank=True, null=True)
    smtp_enabled = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    CACHE_KEY = "gitsap:config"

    class Meta:
        db_table = "config"

    @property
    def application_version(self):
        pyproject_path = settings.BASE_DIR / "pyproject.toml"

        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)

        return pyproject.get("project").get("version")

    @classmethod
    def get_factory_instance(cls):
        return cls.objects.get(pk=1)

    @classmethod
    def cached_instance(cls):
        config = cache.get(cls.CACHE_KEY)

        if config is None:
            config, _ = cls.objects.get_or_create(
                pk=1,
                defaults={
                    "organization_name": "Gitsap",
                    "support_email_address": "setup@gitsap.com",
                },
            )
            cache.set(cls.CACHE_KEY, config)

        return config
