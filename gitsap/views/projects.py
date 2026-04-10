from django.views import View
from django.shortcuts import render

from gitsap.mixins import ProjectAccessMixin


class RepoView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "code"}
        return render(request, "projects/repo.html", context)


class CommitsView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "commits"}
        return render(request, "projects/commits.html", context)


class BranchesView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {"namespace": kwargs["namespace"], "current_page": "branches"}
        return render(request, "projects/branches.html", context)


class SettingsGeneralView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {
            "namespace": kwargs["namespace"],
            "current_page": "settings",
            "current_settings_page": "general",
        }
        return render(request, "projects/settings/general.html", context)


class SettingsCollaboratorsView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {
            "namespace": kwargs["namespace"],
            "current_page": "settings",
            "current_settings_page": "collaborators",
        }
        return render(request, "projects/settings/collaborators.html", context)


class SettingsBranchesView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {
            "namespace": kwargs["namespace"],
            "current_page": "settings",
            "current_settings_page": "branches",
        }
        return render(request, "projects/settings/branches.html", context)


class SettingsRulesView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {
            "namespace": kwargs["namespace"],
            "current_page": "settings",
            "current_settings_page": "rules",
        }
        return render(request, "projects/settings/rules.html", context)


class SettingsEnvironmentsView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {
            "namespace": kwargs["namespace"],
            "current_page": "settings",
            "current_settings_page": "environments",
        }
        return render(request, "projects/settings/environments.html", context)


class SettingsWebhooksView(ProjectAccessMixin, View):
    def get(self, request, **kwargs):
        context = {
            "namespace": kwargs["namespace"],
            "current_page": "settings",
            "current_settings_page": "webhooks",
        }
        return render(request, "projects/settings/webhooks.html", context)
