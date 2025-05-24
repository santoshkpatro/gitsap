from django import forms
from django.utils.html import strip_tags

from gitsap.accounts.models import User


class IssueCreateForm(forms.Form):
    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter a title for the issue",
                "required": "required",
            }
        )
    )
    summary_html = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control d-none",
                "placeholder": "Write a summary of the issue",
            }
        )
    )

    assignees = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # We'll set this in the view
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "hidden": True,
                "id": "user-hidden-select",  # consistent with data-select
            }
        ),
        label="Assignees",
    )

    def clean_summary_html(self):
        html = self.cleaned_data.get("summary_html", "").strip()
        if not strip_tags(html).strip():
            return None
        return html

    def clean(self):
        cleaned_data = super().clean()
        summary_html = cleaned_data.get("summary_html")
        if summary_html:
            cleaned_data["summary"] = strip_tags(summary_html).strip() or None
        else:
            cleaned_data["summary"] = None
        return cleaned_data


class IssueCommentCreateForm(forms.Form):
    content_html = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control d-none",
                "placeholder": "Write a comment",
            }
        ),
        required=True,
    )

    def clean_content_html(self):
        html = self.cleaned_data.get("content_html", "").strip()
        if not strip_tags(html).strip():
            return None
        return html

    def clean(self):
        cleaned_data = super().clean()
        content_html = cleaned_data.get("content_html")
        if content_html:
            cleaned_data["content"] = strip_tags(content_html).strip() or None
        else:
            cleaned_data["content"] = None
        return cleaned_data
