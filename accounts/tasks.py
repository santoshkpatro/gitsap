from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings

from accounts.models import User


@shared_task
def send_account_verification_email(email):
    user = User.objects.filter(email=email).first()
    if not user:
        return

    context = {"user": user, "current_year": timezone.now().year}
    html_message = render_to_string("accounts/emails/verification.html", context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            "Account Verification",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        print("Exception", e)


@shared_task
def send_welcome_email(email):
    user = User.objects.filter(email=email).first()
    if not user:
        return
    context = {"current_year": timezone.now().year}
    html_message = render_to_string("accounts/emails/welcome.html", context)
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            "Welcome to Gitsap",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        print("Exception", e)
