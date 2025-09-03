from django.views import View
from django.shortcuts import redirect, render
from django.contrib.auth import logout as user_logout


class LoginView(View):
    def get(self, request):
        next = request.GET.get("next", "/")
        return render(request, "users/login.html", {"next": next})


# class RegisterView(View):
#     def get(self, request):
#         return vite_render(request, "pages/users/register.js")


# class LogoutView(View):
#     def get(self, request):
#         user_logout(request)
#         return redirect("login")
