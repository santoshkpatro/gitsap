from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.db import transaction
from django.conf import settings
from django.contrib.auth import login


from gitsap.config.models import Config
from gitsap.config.forms import (
    ConfigOnboardingOrganizationForm,
    ConfigOnboardingAdminForm,
    ConfigOnboardingSmtpForm,
)
from gitsap.accounts.models import User

class ConfigOnboardingView(View):

    SESSION_KEY = "config-onboarding"

    STEPS = {
        "organization": {
            "form": ConfigOnboardingOrganizationForm,
            "required": True,
        },
        "admin": {
            "form": ConfigOnboardingAdminForm,
            "required": True,
        },
        "smtp": {
            "form": ConfigOnboardingSmtpForm,
            "required": False,
        },
    }

    def dispatch(self, request, *args, **kwargs):
        config = Config.get_factory_instance()
        if config.is_onboarded:
            messages.info(request, "Configuration has already been completed.")
            return redirect("root-home")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        step = kwargs.get("step")
        steps = list(self.STEPS.keys())
        if step not in steps:
            messages.error(
                request,
                "Invalid step found, please try to fill it again. Redirecting to onboarding",
            )
            return redirect("config-onboarding", step="organization")

        request.session.setdefault(
            self.SESSION_KEY,
            {step: {} for step in steps},
        )

        existing_filled_data = request.session[self.SESSION_KEY].get(step, {})

        FormClass = self.STEPS[step].get("form")
        form = FormClass(initial=existing_filled_data)
        step_index = steps.index(step)

        context = {
            "form": form,
            "prev_step_name": steps[step_index - 1] if step_index != 0 else None,
        }
        return render(request, "config/config_onboarding_{}.html".format(step), context)

    def post(self, request, **kwargs):
        step = kwargs.get("step")
        steps = list(self.STEPS.keys())
        if step not in steps:
            messages.error(
                request,
                "Invalid step found, please try to fill it again. Redirecting to onboarding",
            )
            return redirect("config-onboarding", step="organization")

        FormClass = self.STEPS[step].get("form")
        form = FormClass(data=request.POST)
        step_index = steps.index(step)

        if not form.is_valid():
            context = {
                "form": form,
                "prev_step_name": steps[step_index - 1] if step_index != 0 else None,
            }
            return render(
                request, "config/config_onboarding_{}.html".format(step), context
            )

        cleaned_data = form.cleaned_data
        request.session[self.SESSION_KEY][step] = cleaned_data
        request.session.modified = True

        if step != "smtp":
            return redirect("config-onboarding", step=steps[step_index + 1])

        config_payload = request.session[self.SESSION_KEY]
        config = Config.get_factory_instance()
        with transaction.atomic():
            admin_user = User.create_admin_user(**config_payload.get("admin"))
            for k, v in config_payload.get("organization").items():
                setattr(config, k, v)

            for k, v in config_payload.get("smtp").items():
                setattr(config, k, v)

            config.is_onboarded = True
            config.save()
            del request.session[self.SESSION_KEY]
            login(request, admin_user)

        return redirect("root-home")

