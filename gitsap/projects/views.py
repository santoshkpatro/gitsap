import markdown
from collections import defaultdict
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.text import slugify
from django.urls import reverse
from django.shortcuts import get_object_or_404

from gitsap.projects.models import Project
from gitsap.projects.forms import ProjectCreateForm
from gitsap.projects.mixins import ProjectAccessMixin
from gitsap.organizations.models import Organization


class ProjectCreateView(LoginRequiredMixin, View):
    def get_owner_choices(self, user):
        organizations = Organization.objects.filter(
            users__user=user, users__role__in=["owner", "admin"]
        )
        return [(user.username, f"You ({user.username})")] + [
            (org.slug, org.name) for org in organizations
        ]

    def get(self, request, *args, **kwargs):
        form = ProjectCreateForm()
        form.fields["owner"].choices = self.get_owner_choices(request.user)
        context = {
            "form": form,
        }
        return render(request, "projects/create.html", context)

    def post(self, request, *args, **kwargs):
        form = ProjectCreateForm(request.POST)
        form.fields["owner"].choices = self.get_owner_choices(request.user)

        context = {"form": form}
        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return render(request, "projects/create.html", context)

        cleaned_data = form.cleaned_data
        owner_slug = cleaned_data.pop("owner")
        project_handle = slugify(cleaned_data["name"])

        # Check if the project with this handle already exists under this owner
        existing_project = Project.objects.filter(
            namespace=owner_slug, handle=project_handle
        )
        if existing_project.exists():
            form.add_error("name", "You already have a project with this name.")
            return render(request, "projects/create.html", context)

        project = Project(**cleaned_data)
        project.handle = project_handle
        project.created_by = request.user

        if owner_slug == request.user.username:
            project.user = request.user
            project.namespace = request.user.username
        else:
            # Assuming user has access to orgs, otherwise return 404 or permission denied
            organization = get_object_or_404(Organization, slug=owner_slug)
            project.organization = organization
            project.namespace = organization.slug

        project.save()

        return redirect(
            "project-overview",
            namespace=project.namespace,
            handle=project.handle,
        )


class ProjectOverview(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")

        project = request.project
        current_ref = request.GET.get("ref", project.default_branch)
        tree_browsable_path = reverse(
            "project-tree",
            args=[project.namespace, project.handle, current_ref],
        )
        blob_browsable_path = reverse(
            "project-blob",
            args=[project.namespace, project.handle, current_ref],
        )

        git_service = project.git_service
        repo_objects = git_service.get_tree_objects_at_path(
            ref_name=current_ref,
            relative_path="",
        )

        # Detect readme-like blob (case-insensitive)
        readme_blob = next(
            (
                obj
                for obj in repo_objects
                if obj["type"] == "blob" and obj["name"].lower().startswith("readme")
            ),
            None,
        )

        # Get README content if found
        readme_content = None
        if readme_blob:
            try:
                readme = git_service.get_blob_at_path(
                    ref_name=current_ref, relative_path=readme_blob["name"]
                )
                readme_content = markdown.markdown(readme["content"].decode("utf-8"))
            except Exception:
                # Optionally log or handle error if blob retrieval fails
                pass

        context = {
            "project": project,
            "repo_objects": repo_objects,
            "current_ref": current_ref,
            "tree_browsable_path": tree_browsable_path,
            "blob_browsable_path": blob_browsable_path,
            "last_commit": git_service.get_last_commit_info_for_ref(
                project.default_branch
            ),
            "active_tab": "code",
            "commits_count": git_service.get_commits_count(current_ref),
            "readme_content": readme_content,
        }
        return render(request, "projects/overview.html", context)


class ProjectTreeView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")

        project = request.project
        git_service = project.git_service

        ref_and_path = kwargs.get("ref_and_path", "")
        ref, relative_path = git_service.resolve_ref_and_path(ref_and_path)

        repo_objects = git_service.get_tree_objects_at_path(
            ref_name=ref,
            relative_path=relative_path.strip("/"),
        )
        tree_browsable_path = reverse(
            "project-tree",
            args=[project.namespace, project.handle, ref_and_path],
        )
        blob_browsable_path = reverse(
            "project-blob",
            args=[project.namespace, project.handle, ref_and_path],
        )

        context = {
            "project": project,
            "repo_objects": repo_objects,
            "tree_browsable_path": tree_browsable_path,
            "blob_browsable_path": blob_browsable_path,
            "last_commit": git_service.get_last_commit_info(
                relative_path.strip("/"), ref
            ),
            "active_tab": "code",
        }
        return render(request, "projects/tree.html", context)


class ProjectBlobView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")

        project = request.project
        git_service = project.git_service

        ref_and_path = kwargs.get("ref_and_path", "")
        ref, relative_path = git_service.resolve_ref_and_path(ref_and_path)

        repo_object = git_service.get_blob_at_path(
            ref_name=ref,
            relative_path=relative_path.strip("/"),
        )

        context = {
            "project": project,
            "repo_object": repo_object,
            "current_ref": ref,
            "last_commit": git_service.get_last_commit_info(relative_path, ref),
            "active_tab": "code",
        }
        return render(request, "projects/blob.html", context)


class ProjectCommitHistoryView(ProjectAccessMixin, View):
    def get(self, request, *args, **kwargs):
        self.require_permission(request, "can_read")

        project = request.project
        git_service = project.git_service

        ref = kwargs.get("ref")
        skip = int(request.GET.get("skip", 0))
        commit_history = git_service.get_commit_history(ref, max_count=21, skip=skip)

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
