from django.views import View

from gitsap.utils.template import vite_render



class LoginView(View):
    def get(self, request):
        next_url = request.GET.get("next", "/accounts/profile/")
        return vite_render(request, "pages/users/login.js", {"next_url": next_url})