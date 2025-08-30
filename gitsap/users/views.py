from django.views import View
from django.shortcuts import redirect
from django.contrib.auth import logout as user_logout

from gitsap.utils.template import vite_render


class LoginView(View):
    def get(self, request):
        next_url = request.GET.get("next", "/accounts/profile/")
        return vite_render(request, "pages/users/login.js", {"next_url": next_url})


class RegisterView(View):
    def get(self, request):
        return vite_render(request, "pages/users/register.js")


class LogoutView(View):
    def get(self, request):
        user_logout(request)
        return redirect("login")
