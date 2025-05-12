from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from projects.models import Project, ProjectCollaborator


class ProjectAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        username = kwargs.get("username")
        project_handle = kwargs.get("project_handle")

        project = get_object_or_404(
            Project, owner__username=username, handle=project_handle
        )
        request.project = project
        request.project_collaborator_role = None

        if request.user.is_authenticated:
            try:
                collaborator = ProjectCollaborator.objects.get(
                    project=project, user=request.user
                )
                request.project_collaborator_role = collaborator.role
            except ProjectCollaborator.DoesNotExist:
                pass

        # Enforce access if private
        if project.visibility == Project.Visibility.PRIVATE:
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required to view this project.")

            if request.project_collaborator_role is None:
                raise PermissionDenied(
                    "You do not have permission to view this project."
                )

        return super().dispatch(request, *args, **kwargs)

    def require_collaborator(self, request):
        """
        Enforce collaborator or owner-only access.
        """
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required to modify this project.")

        if not request.project_collaborator_role:
            raise PermissionDenied(
                "You must be a collaborator or owner to perform this action."
            )
