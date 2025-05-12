from collections import defaultdict
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.text import slugify
from django.urls import reverse

from projects.models import Project
from projects.forms import ProjectCreateForm
from projects.mixins import ProjectAccessMixin


class ProjectCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = {
            "form": ProjectCreateForm(),
        }
        return render(request, "projects/create.html", context)

    def post(self, request, *args, **kwargs):
        form = ProjectCreateForm(request.POST)
        context = {"form": form}
        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return render(request, "projects/create.html", context)

        cleaned_data = form.cleaned_data
        existing_project = Project.objects.filter(
            owner=request.user, handle=slugify(cleaned_data["name"])
        )
        if existing_project.exists():
            form.add_error("name", "You already have a project with this name.")
            return render(request, "projects/create.html", context)

        project = Project(
            **cleaned_data,
        )
        project.owner = request.user
        project.save()

        return redirect(
            "project-overview",
            username=request.user.username,
            project_handle=project.handle,
        )


class ProjectOverview(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        current_ref = request.GET.get("ref", project.default_branch)
        tree_browsable_path = reverse(
            "project-tree", args=[project.owner.username, project.handle, current_ref]
        )
        blob_browsable_path = reverse(
            "project-blob",
            args=[project.owner.username, project.handle, current_ref],
        )

        context = {
            "project": project,
            "repo_objects": project.get_tree_objects_at_path(
                ref_name=current_ref,
                relative_path="",
            ),
            "current_ref": current_ref,
            "tree_browsable_path": tree_browsable_path,
            "blob_browsable_path": blob_browsable_path,
            "last_commit": project.get_last_commit_info_for_ref(project.default_branch),
            "active_tab": "code",
            "commits_count": project.get_commits_count(current_ref),
        }
        return render(request, "projects/overview.html", context)


class ProjectTreeView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project

        ref_and_path = kwargs.get("ref_and_path", "")
        ref, relative_path = project.resolve_ref_and_path(ref_and_path)

        repo_objects = project.get_tree_objects_at_path(
            ref_name=ref,
            relative_path=relative_path.strip("/"),
        )
        tree_browsable_path = reverse(
            "project-tree",
            args=[project.owner.username, project.handle, ref_and_path],
        )
        blob_browsable_path = reverse(
            "project-blob",
            args=[project.owner.username, project.handle, ref_and_path],
        )

        context = {
            "project": project,
            "repo_objects": repo_objects,
            "tree_browsable_path": tree_browsable_path,
            "blob_browsable_path": blob_browsable_path,
            "last_commit": project.get_last_commit_info(relative_path.strip("/"), ref),
            "active_tab": "code",
        }
        return render(request, "projects/tree.html", context)


class ProjectBlobView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        ref_and_path = kwargs.get("ref_and_path", "")
        ref, relative_path = project.resolve_ref_and_path(ref_and_path)

        repo_object = project.get_blob_at_path(
            ref_name=ref,
            relative_path=relative_path.strip("/"),
        )

        context = {
            "project": project,
            "repo_object": repo_object,
            "current_ref": ref,
            "last_commit": project.get_last_commit_info(relative_path, ref),
            "active_tab": "code",
        }
        return render(request, "projects/blob.html", context)


class ProjectCommitHistoryView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        project = request.project
        ref = kwargs.get("ref")
        skip = int(request.GET.get("skip", 0))
        commit_history = project.get_commit_history(ref, max_count=21, skip=skip)

        visible_commits = commit_history[:20]
        has_more = len(commit_history) > 20

        grouped_commits = defaultdict(list)
        for commit in visible_commits:
            local_date = commit["timestamp"].date()
            grouped_commits[local_date].append(commit)

        context = {
            "project": project,
            "grouped_commits": dict(grouped_commits),
            "current_ref": ref,
            "active_tab": "code",
            "has_more": has_more,
            "next_skip": skip + 20,
            "prev_skip": max(0, skip - 20),
            "skip": skip,
        }
        return render(request, "projects/commit_history.html", context)
