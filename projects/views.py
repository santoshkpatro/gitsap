from django.shortcuts import render
from django.views import View


class ProjectOverview(View):
    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, "projects/overview.html", context)
