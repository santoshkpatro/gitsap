from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render


class IndexView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, "home/index.html", context)
