from django import forms


class LoginForm(forms.Form):
    identity = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "username or email",
                "required": "required",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "Enter password",
                "required": "required",
            }
        ),
    )


class RegisterForm(forms.Form):
    full_name = forms.CharField(
        label="Full Name",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "Full Name",
                "required": "required",
            }
        ),
    )
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "Username",
                "required": "required",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "Email",
                "required": "required",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "Enter password",
                "required": "required",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control border-start-0",
                "placeholder": "Confirm password",
                "required": "required",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        # Remove confirm_password from final cleaned_data
        cleaned_data.pop("confirm_password", None)

        return cleaned_data
