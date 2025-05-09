from django import forms


class ProjectCreateForm(forms.Form):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
    ]

    name = forms.CharField(
        label="Project name",
        max_length=128,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    visibility = forms.CharField(
        label="Visibility",
        widget=forms.HiddenInput(),  # We'll render radios manually
    )

    description = forms.CharField(
        label="Description (optional)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Write a short description…",
                "rows": 1,
            }
        ),
    )
