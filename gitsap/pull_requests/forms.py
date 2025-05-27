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
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Write a description for the pull request",
                "rows": 3,
            }
        ),
        required=False,
    )
    source_branch = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "form-control"}), required=True
    )
    target_branch = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "form-control"}), required=True
    )

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        return description if description else None


class PullRequestMergeConfirmForm(forms.Form):
    commit_message = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter a commit message",
                "required": "required",
            }
        ),
        required=True,
    )


class PullRequestCommentForm(forms.Form):
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
