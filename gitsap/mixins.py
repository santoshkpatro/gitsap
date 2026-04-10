from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from gitsap.models import Project, ProjectVisibilityChoice


class ProjectAccessMixin:
    """
    Resolves the project from the URL namespace and enforces visibility /
    permission rules before the view handler runs.

    Attaches to request:
        request.project          — always
        request.organization     — when project belongs to an org
        request.organization_role — role string, when org permission exists
        request.project_role     — role string, when direct project permission exists
    """

    def dispatch(self, request, **kwargs):
        project = get_object_or_404(Project, namespace=kwargs["namespace"])
        request.project = project

        visibility = project.visibility

        # Public projects are accessible to everyone
        if visibility == ProjectVisibilityChoice.PUBLIC:
            self._attach_permission(request, project)
            return super().dispatch(request, **kwargs)

        # Internal and private require authentication
        if not request.user.is_authenticated:
            return redirect("login")

        # Internal projects are accessible to any authenticated user
        if visibility == ProjectVisibilityChoice.INTERNAL:
            self._attach_permission(request, project)
            return super().dispatch(request, **kwargs)

        # Private: must have explicit org or project-level permission
        if visibility == ProjectVisibilityChoice.PRIVATE:
            if not self._attach_permission(request, project):
                return HttpResponseForbidden()
            return super().dispatch(request, **kwargs)

        return HttpResponseForbidden()

    def _attach_permission(self, request, project):
        """
        Attaches permission context to the request.
        Returns True if the user has an explicit permission record, False otherwise.
        For unauthenticated users always returns False without querying the DB.
        """
        if not request.user.is_authenticated:
            return False

        if project.organization_id:
            request.organization = project.organization
            org_permission = (
                project.organization.permissions
                .filter(user=request.user)
                .first()
            )
            if org_permission:
                request.organization_role = org_permission.role
                return True
            return False

        project_permission = (
            project.permissions
            .filter(user=request.user)
            .first()
        )
        if project_permission:
            request.project_role = project_permission.role
            return True

        return False
