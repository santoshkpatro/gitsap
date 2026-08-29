from django.shortcuts import render, redirect
from django.views import View

from gitsap.config.models import Config


class RootHomeView(View):
    def get(self, request, **kwargs):
        if not Config.objects.values_list(
            "is_onboarded",
            flat=True,
        ).get(pk=1):
            return redirect("config-onboarding", step="organization")
        return render(request, "root/root_home.html")


class RootHealthView(View):
    def get(self, request, **kwargs):
        return render(request, "root/root_health.html")
