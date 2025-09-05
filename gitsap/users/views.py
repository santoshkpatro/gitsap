from django.views import View
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe

from gitsap.users.forms import LoginForm, RegisterForm
from gitsap.users.models import User


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        context = {"form": form}
        return render(request, "users/register.html", context)


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, "users/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please correct the errors in the form.")
            return render(request, "users/login.html", {"form": form})

        login_data = form.cleaned_data
        identity = login_data["identity"]
        password = login_data["password"]

        # Lookup by email or username
        lookup_field = "email" if "@" in identity else "username"
        user = User.objects.filter(**{lookup_field: identity}).first()

        if not user:
            messages.error(request, "We couldn’t find an account with those details.")
            return render(request, "users/login.html", {"form": form})

        # Account suspension
        if user.suspended_at:
            messages.error(
                request, "Your account has been suspended. Please contact support."
            )
            return render(request, "users/login.html", {"form": form})

        # Account locked due to failed attempts
        if user.locked_until and user.locked_until > timezone.now():
            messages.error(
                request,
                "Your account is temporarily locked due to too many failed login attempts. Try again later.",
            )
            return render(request, "users/login.html", {"form": form})

        # Account activation/verification checks
        if not user.verified_at:
            messages.error(
                request,
                mark_safe(
                    "Your account is not activated yet. Please check your email for the verification link. Didn't receive it? <a href='{}'>Resend verification email</a>.".format(
                        user.resend_verification_link
                    )
                ),
            )
            return render(request, "users/login.html", {"form": form})

        # Password check
        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:  # Example threshold
                user.locked_until = timezone.now() + timezone.timedelta(minutes=15)
                messages.error(
                    request,
                    "Too many failed attempts. Your account has been locked for 15 minutes.",
                )
            else:
                messages.error(request, "The password you entered is incorrect.")
            user.save(update_fields=["failed_login_attempts", "locked_until"])
            return render(request, "users/login.html", {"form": form})

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_ip = request.META.get("REMOTE_ADDR")
        user.last_login = timezone.now()
        user.save(
            update_fields=["failed_login_attempts", "last_login", "last_login_ip"]
        )

        # Successful login
        login(request, user)
        messages.success(request, f"Welcome back, {user.full_name or user.username}!")
        return redirect("users-login")  # Redirect to your main dashboard


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("users-login")


class UsernameCheckView(APIView):
    def get(self, request):
        username = request.query_params.get("username", "").strip()
        if not username:
            return Response(
                {"available": False, "message": "Username is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"available": False, "message": "This username is already taken."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"available": True, "message": "This username is available!"},
            status=status.HTTP_200_OK,
        )


class VerificationConfirmView(View):
    def get(self, request, uidb64, token):
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.filter(pk=uid, verified_at__isnull=True).first()
        if not user:
            messages.error(
                request, "The verification link is either invalid or has expired."
            )
            return redirect("users-login")

        if user.verify(token):
            messages.success(
                request, "Your account has been verified. You can now log in."
            )
            return redirect("users-login")
        else:
            messages.error(
                request, "The verification link is either invalid or has expired."
            )
            return redirect("users-login")


class VerificationResendView(View):
    def get(self, request, uidb64):
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.filter(pk=uid, verified_at__isnull=True).first()
        if not user:
            messages.error(
                request, "The account is either already verified or does not exist."
            )
            return redirect("users-login")

        # Resend the verification email
        # (Assuming you have a function send_verification_email)
        # send_verification_email(user)

        messages.success(
            request,
            "A new verification email has been sent to your registered email address. Please check your inbox and spam folder.",
        )
        return redirect("users-login")
