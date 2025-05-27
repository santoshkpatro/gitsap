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

    summary = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Write a summary of the issue",
                "rows": 3,
            }
        ),
        required=False,
    )

    def clean_summary(self):
        summary = self.cleaned_data.get("summary", "").strip()
        return summary if summary else None


class IssueCommentCreateForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control d-none",
                "placeholder": "Write a comment",
            }
        ),
        required=True,
    )

    def clean_content(self):
        return self.cleaned_data.get("content", "").strip()
