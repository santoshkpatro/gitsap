from django.views import View
from django.shortcuts import redirect, render
from django.contrib.auth import logout, login
from django.contrib import messages


from gitsap.users.forms import LoginForm


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        context = {"form": form, "next": next}
        return render(request, "users/login.html", context)

    def post(self, request):
        form = LoginForm(request.POST)
        context = {"form": form}
        if not form.is_valid():
            messages.error(request, "Invalid form submission.")
            return render(request, "users/login.html", context)

        # Validate
        messages.success(request, "Login successful.")
        return redirect("users-login")
