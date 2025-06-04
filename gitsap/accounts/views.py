from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, logout
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin

from gitsap.accounts.models import User
from gitsap.accounts.forms import LoginForm, RegisterForm, ProfileForm
from gitsap.accounts.tasks import send_account_verification_email, send_welcome_email
from gitsap.attachments.models import Attachment


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        context = {"form": form}
        return render(request, "accounts/login.html", context)

    def post(self, request):
        context = {}
        form = LoginForm(request.POST)
        context["form"] = form

        if not form.is_valid():
            messages.error(request, "Please enter a valid username and password.")
            return render(request, "accounts/login.html", context)

        cleaned_data = form.cleaned_data
        username = cleaned_data.get("username")
        # Check for @ in username
        if "@" in username:
            query = {"email": username}
        else:
            query = {"username": username}

        # Check if user exists
        user = User.objects.filter(**query).first()
        if not user:
            form.add_error("username", "No account found with this username or email.")
            return render(request, "accounts/login.html", context)

        if not user.is_active:
            form.add_error("username", "No account found with this username or email.")
            return render(request, "accounts/login.html", context)

        if not user.is_verified:
            email_verification_resend_url = (
                reverse("accounts-email-verification-resend") + f"?email={user.email}"
            )
            messages.warning(
                request,
                f"We’ve already sent a verification link to your email. "
                f"If you haven’t received it, <a href='{email_verification_resend_url}'>click here</a> to request a new one.",
            )
            return render(request, "accounts/login.html", context)

        # Check if password is correct
        password = cleaned_data.get("password")
        if not user.check_password(password):
            form.add_error("password", "The password you entered is incorrect.")
            return render(request, "accounts/login.html", context)

        login(request, user)
        return redirect("home-index")


class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        context = {"form": form}
        return render(request, "accounts/register.html", context)

    def post(self, request):
        form = RegisterForm(request.POST)
        context = {"form": form}

        if not form.is_valid():
            messages.error(request, "Please correct the errors below and try again.")
            return render(request, "accounts/register.html", context)

        cleaned_data = form.cleaned_data
        email = cleaned_data.get("email")
        password1 = cleaned_data.pop("password1")
        password2 = cleaned_data.pop("password2")

        if not password1 or not password2:
            form.add_error("password2", "Please confirm your password.")
            return render(request, "accounts/register.html", context)

        user = User.objects.filter(email=email).first()
        if user and user.is_active:
            form.add_error("email", "An account with this email already exists.")
            return render(request, "accounts/register.html", context)

        # Check if passwords match
        if password1 != password2:
            form.add_error("password2", "Passwords do not match.")
            return render(request, "accounts/register.html", context)

        # Create user
        if user is None:
            user = User(
                email=email,
                first_name=cleaned_data.get("first_name"),
                last_name=cleaned_data.get("last_name", None),
            )
        else:
            user.first_name = cleaned_data.get("first_name")
            user.last_name = cleaned_data.get("last_name", None)

        user.activated_at = timezone.now()
        user.set_password(password1)
        user.save()

        send_account_verification_email.delay(user.email)

        messages.success(
            request,
            "Your account has been created successfully. "
            "Please check your email inbox (including spam) to verify your account before logging in.",
        )
        return redirect("accounts-login")


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("accounts-login")


class EmailVerificationConfirmView(View):
    def get(self, request, *args, **kwargs):
        uidb64 = kwargs.get("uidb64")
        token = kwargs.get("token")

        # Write the logic to verify
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(id=uid)
        except Exception:
            user = None

        if user and default_token_generator.check_token(user, token):
            user.verified_at = timezone.now()
            user.save(update_fields=["verified_at"])
            messages.success(request, "Your email has been successfully verified.")
            send_welcome_email.delay(user.email)
            login(request, user)
            return redirect("home-index")

        return HttpResponse(
            "This verification link is invalid or has expired.", status=400
        )


class EmailVerificationResendConfirmView(View):
    def get(self, request, *args, **kwargs):
        email = request.GET.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            messages.warning(request, "No account found with this email address.")
            return redirect("accounts-login")

        if user.is_verified:
            messages.warning(request, "This account has already been verified.")
            return redirect("accounts-login")

        send_account_verification_email.delay(user.email)
        messages.success(
            request,
            "A new verification link has been sent to your email. Please check your inbox and spam folder.",
        )
        return redirect("accounts-login")


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = ProfileForm(
            instance=request.user,
        )
        context = {"form": form, "active_tab": "profile"}
        return render(request, "accounts/profile.html", context)

    def post(self, request):
        form = ProfileForm(data=request.POST)
        if not form.is_valid():
            messages.error(request, "Please correct the errors below and try again.")
            context = {"form": form, "active_tab": "profile"}
            return render(request, "accounts/profile.html", context)

        changed, errors = request.user.apply_updates(form.cleaned_data)
        if errors:
            messages.error(
                request, "There were errors updating your profile: " + ", ".join(errors)
            )
        else:
            messages.success(
                request, "Profile updated successfully!", extra_tags="toast"
            )
        return redirect("accounts-profile")
