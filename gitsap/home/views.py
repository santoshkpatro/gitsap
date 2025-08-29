from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from gitsap.utils.template import vite_render


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        return vite_render(request, "pages/home/index.js")
