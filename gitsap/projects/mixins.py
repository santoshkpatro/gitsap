from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from gitsap.projects.models import Project, ProjectCollaborator
from gitsap.organizations.models import OrganizationUser
from django.http import Http404


class ProjectAccessMixin:
    def dispatch(self, request, *args, **kwargs):
        namespace = kwargs.get("namespace")
        handle = kwargs.get("handle")

        project = get_object_or_404(Project, namespace=namespace, handle=handle)
        request.project = project

        request.project_permissions = {
            "can_read": False,
            "can_write": False,
            "can_admin": False,
        }

        if not request.user.is_authenticated:
            if project.visibility == Project.Visibility.PRIVATE:
                raise Http404

            request.project_permissions["can_read"] = True
            return super().dispatch(request, *args, **kwargs)

        # 1. Owned by user
        if project.owner_type == "user" and project.user == request.user:
            request.project_permissions.update(
                {
                    "can_read": True,
                    "can_write": True,
                    "can_admin": True,
                }
            )
        # 2. Owned by organization
        elif project.owner_type == "organization":
            try:
                org_user = OrganizationUser.objects.get(
                    organization=project.organization, user=request.user
                )
                if org_user.role in [
                    OrganizationUser.Role.OWNER,
                    OrganizationUser.Role.ADMIN,
                ]:
                    request.project_permissions.update(
                        {
                            "can_read": True,
                            "can_write": True,
                            "can_admin": True,
                        }
                    )
                elif org_user.role == OrganizationUser.Role.MAINTAINER:
                    request.project_permissions.update(
                        {
                            "can_read": True,
                            "can_write": True,
                            "can_admin": False,
                        }
                    )
                elif org_user.role == OrganizationUser.Role.DEVELOPER:
                    request.project_permissions.update(
                        {
                            "can_read": True,
                            "can_write": True,
                            "can_admin": False,
                        }
                    )
            except OrganizationUser.DoesNotExist:
                pass

        # 3. Collaborator
        try:
            collaborator = ProjectCollaborator.objects.get(
                project=project, user=request.user
            )
            if collaborator.role == "owner":
                request.project_permissions.update(
                    {
                        "can_read": True,
                        "can_write": True,
                        "can_admin": True,
                    }
                )

            elif collaborator.role == "collaborator":
                request.project_permissions.update(
                    {
                        "can_read": True,
                        "can_write": True,
                        "can_admin": False,
                    }
                )
        except ProjectCollaborator.DoesNotExist:
            pass

        return super().dispatch(request, *args, **kwargs)

    def require_permission(self, request, perm):
        if not request.project_permissions.get(perm):
            raise PermissionDenied(f"Missing required permission: {perm}")
