from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from gitsap.accounts.models import User
from gitsap.config.models import Config


class ConfigOnboardingOrganizationForm(forms.Form):
    organization_name = forms.CharField(
        label="Organization name",
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Acme Inc.",
            }
        ),
    )

    support_email = forms.EmailField(
        label="Support email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "support@acme.com",
            }
        ),
    )

    application_url = forms.URLField(
        label="Application URL",
        required=False,
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://app.acme.com",
            }
        ),
    )


class ConfigOnboardingAdminForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=128,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "admin",
            }
        ),
    )

    email_address = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "admin@acme.com",
            }
        ),
    )

    full_name = forms.CharField(
        label="Full name",
        max_length=128,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Jane Doe",
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email_address=email).exists():
            raise ValidationError("A user with this email address already exists.")

        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data


class ConfigOnboardingSmtpForm(forms.Form):
    enabled = forms.BooleanField(
        label="Enable SMTP email delivery",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    host = forms.CharField(
        label="SMTP host",
        max_length=128,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "smtp.sendgrid.net",
            }
        ),
    )

    port = forms.IntegerField(
        label="SMTP port",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "587",
            }
        ),
    )

    username = forms.CharField(
        label="SMTP username",
        max_length=128,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "apikey",
            }
        ),
    )

    password = forms.CharField(
        label="SMTP password",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    encryption = forms.ChoiceField(
        label="Encryption",
        choices=Config.SMTPEncryption.choices,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    default_from_email = forms.EmailField(
        label="Default from email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "no-reply@acme.com",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("enabled"):
            for field in ("host", "port", "default_from_email"):
                if not cleaned_data.get(field):
                    self.add_error(field, "Required when SMTP is enabled.")

        return cleaned_data
