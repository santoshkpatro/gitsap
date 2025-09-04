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
