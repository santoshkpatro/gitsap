from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, logout

from accounts.models import User
from accounts.forms import LoginForm


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
            form.add_error(
                "username", "User does not exist with this username or email."
            )
            return render(request, "accounts/login.html", context)

        if not user.is_active:
            form.add_error(
                "username", "User does not exist with this username or email."
            )
            return render(request, "accounts/login.html", context)

        # Check if password is correct
        password = cleaned_data.get("password")
        if not user.check_password(password):
            form.add_error("password", "Password is incorrect.")
            return render(request, "accounts/login.html", context)

        login(request, user)

        return redirect("home-index")
