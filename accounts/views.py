from django.shortcuts import render
from django.views import View

from accounts.forms import LoginForm


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        context = {"form": form}
        return render(request, "accounts/login.html", context)
