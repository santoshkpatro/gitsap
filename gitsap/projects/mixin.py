from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.http import Http404

from gitsap.projects.models import Project, ProjectPermission


class ProjectPermissionMixin:
    """
    A mixin for project-scoped views with role-based and visibility checks.
    """

    # Possible values: 'read', 'write', 'admin', 'owner', 'triage', 'maintain'
    # This roles need to be defined by the view using this mixin and mainly used for private projects.
    allowed_roles = []

    @cached_property
    def project(self):
        namespace = self.kwargs.get("namespace")
        return get_object_or_404(Project, namespace=namespace)

    @cached_property
    def project_permission(self):
        """Return the ProjectPermission for the user, or None if not set."""
        user = self.request.user
        if not user.is_authenticated:
            return None
        return ProjectPermission.objects.filter(project=self.project, user=user).first()

    def dispatch(self, request, *args, **kwargs):
        project = self.project
        request.project = project

        if project.visibility == Project.Visibility.PRIVATE:
            if not request.user.is_authenticated:
                raise Http404()

            if self.project_permission is None:
                raise Http404()

            if self.project_permission.role not in self.allowed_roles:
                raise Http404()

        return super().dispatch(request, *args, **kwargs)
