from django.views import View

from gitsap.utils.template import vite_render



class LoginView(View):
    def get(self, request):
        next_url = request.GET.get("next", "/accounts/profile/")
        return vite_render(request, "js/users/login.js", {"next": next_url})