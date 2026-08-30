from django import forms
from django.utils.text import slugify

from gitsap.projects.models import Project, ProjectVisibility


class ProjectNewForm(forms.Form):
    name = forms.CharField(
        label="Project name",
        max_length=256,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "My awesome project",
            }
        ),
    )

    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "What's this project about?",
            }
        ),
    )

    visibility = forms.ChoiceField(
        label="Visibility",
        choices=ProjectVisibility.choices,
        initial=ProjectVisibility.PRIVATE,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)

        if Project.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                "A project with this name already exists."
            )

        self.cleaned_data["slug"] = slug
        return name
