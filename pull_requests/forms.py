from django import forms
from django.utils.html import strip_tags


class PullRequestCreateForm(forms.Form):
    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter a title for the pull request",
                "required": "required",
            }
        )
    )
    description_html = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control d-none",
                "placeholder": "Write a description about the pull request",
            }
        )
    )
    source_branch = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "form-control"}), required=True
    )
    target_branch = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "form-control"}), required=True
    )

    def clean_description_html(self):
        html = self.cleaned_data.get("description_html", "").strip()
        if not strip_tags(html).strip():
            return None
        return html

    def clean(self):
        cleaned_data = super().clean()
        description_html = cleaned_data.get("description_html")
        if description_html:
            cleaned_data["description"] = strip_tags(description_html).strip() or None
        else:
            cleaned_data["description"] = None
        return cleaned_data
