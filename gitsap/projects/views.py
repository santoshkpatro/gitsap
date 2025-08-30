from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from gitsap.utils.template import vite_render


class ProjectNewView(LoginRequiredMixin, View):
    def get(self, request):
        return vite_render(request, "pages/projects/new.js")
