from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View

from gitsap.projects.forms import ProjectNewForm
from gitsap.projects.models import Project, ProjectMembership, ProjectMembershipRole


class ProjectNewView(LoginRequiredMixin, View):
    def get(self, request, **kwargs):
        form = ProjectNewForm()
        return render(request, "projects/project_new.html", {"form": form})

    def post(self, request, **kwargs):
        form = ProjectNewForm(data=request.POST)

        if not form.is_valid():
            return render(request, "projects/project_new.html", {"form": form})

        cleaned_data = form.cleaned_data
        with transaction.atomic():
            project = Project.objects.create(
                owner=request.user,
                name=cleaned_data["name"],
                slug=cleaned_data["slug"],
                description=cleaned_data["description"],
                visibility=cleaned_data["visibility"],
            )
            ProjectMembership.objects.create(
                project=project,
                user=request.user,
                role=ProjectMembershipRole.OWNER,
                added_by=request.user,
            )

        messages.success(request, "Project created successfully.")
        return redirect("root-home")


class ProjectDetailView(View):
    def get(self, request, **kwargs):
        return render(request, "projects/project_detail.html")