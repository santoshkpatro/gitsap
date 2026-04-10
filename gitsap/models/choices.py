from django.db.models import TextChoices


class UserRoleChoice(TextChoices):
    SUPERUSER = ("superuser", "Superuser")
    USER = ("user", "User")


class ProjectVisibilityChoice(TextChoices):
    PUBLIC = ("public", "Public")
    PRIVATE = ("private", "Private")
    INTERNAL = ("internal", "Internal")


class ProjectRoleChoice(TextChoices):
    OWNER = ("owner", "Owner")
    MAINTAINER = ("maintainer", "Maintainer")
    DEVELOPER = ("developer", "Developer")
    VIEWER = ("viewer", "Viewer")


class GitRefTypeChoice(TextChoices):
    BRANCH = ("branch", "Branch")
    TAG = ("tag", "Tag")
    REMOTE = ("remote", "Remote")


class GitFileChangeTypeChoice(TextChoices):
    ADDED = ("added", "Added")
    MODIFIED = ("modified", "Modified")
    DELETED = ("deleted", "Deleted")
    RENAMED = ("renamed", "Renamed")


class OrganizationPermissionChoice(TextChoices):
    OWNER = ("owner", "Owner")
    ADMIN = ("admin", "Admin")
    MAINTAINER = ("maintainer", "Maintainer")
    COLLABORATOR = ("collaborator", "Collaborator")
    VIEWER = ("viewer", "Viewer")
