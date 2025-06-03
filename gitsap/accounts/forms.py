from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from zoneinfo import available_timezones

from gitsap.accounts.models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your username or email",
                "required": "required",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "*********",
                "required": "required",
            }
        )
    )


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label="First Name",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter first name"}
        ),
    )
    last_name = forms.CharField(
        label="Last Name",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter last name (optional)"}
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your email"}
        ),
    )
    password1 = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Create a password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Repeat password"}
        ),
    )


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name"]

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "is_admin"]


class ProfileForm(forms.Form):
    first_name = forms.CharField(
        label="First Name",
        help_text="Your given name.",
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Last Name",
        help_text="Optional. Your surname or family name.",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    bio = forms.CharField(
        label="Bio",
        help_text="A short description about yourself.",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    website = forms.URLField(
        label="Website",
        help_text="Personal or company website (optional).",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )
    company = forms.CharField(
        label="Company",
        help_text="Your current workplace or organization.",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    timezone = forms.ChoiceField(
        label="Timezone",
        help_text="Set your preferred timezone.",
        choices=[(tz, tz) for tz in sorted(available_timezones())],
        initial="UTC",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    avatar_id = forms.UUIDField(required=False, widget=forms.HiddenInput())
