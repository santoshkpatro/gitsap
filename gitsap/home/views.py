from django.shortcuts import render
from django.views import View
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin

from gitsap.accounts.models import User
from gitsap.organizations.models import Organization
from gitsap.projects.models import Project


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "home/index.html")


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        tab = request.GET.get("tab", "overview")
        valid_tabs = ["overview", "projects", "organizations", "settings"]
        if tab not in valid_tabs:
            raise Http404("Tab not found")        
        is_organization = False

        user_namespace_queryset = User.objects.filter(username=kwargs.get("namespace"))
        org_namespace_queryset = Organization.objects.filter(name=kwargs.get("namespace"))

        if user_namespace_queryset.exists():
            is_organization = True

        if not org_namespace_queryset.exists() and not user_namespace_queryset.exists():
            raise Http404("Namespace not found")

        context = {
            "tab": tab,
            "is_organization": is_organization,
        }
        match tab:
            case "overview":
                projects = Project.objects.filter(namespace=kwargs.get("namespace"), visibility=Project.Visibility.PUBLIC)
                context["projects"] = projects
            case "projects":
                projects = Project.objects.filter(namespace=kwargs.get("namespace"), visibility=Project.Visibility.PUBLIC)
                context["projects"] = projects
            case _:
                raise Http404("Tab not found")
        
        return render(request, f"home/profile/{tab}.html", context)