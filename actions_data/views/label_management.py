from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.forms import modelformset_factory
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.urls import reverse_lazy

from actions_data.models.enums import DateFilterOptions
from actions_data.models import RunnerLabelMultiplier, JobStatsLabel
from actions_data.forms import (
    LabelMultiplierForm,
    LabelMultiplierFormSet as BaseLabelMultiplierFormSet,
)


class BaseLabelManagementView(TemplateView):
    template_name = "actions_data/label_management.html"
    success_url = reverse_lazy("label_management")

    def get_owner(self) -> User:
        return self.request.user

    def get_labels_with_counts(self, user: User):
        """Get all unique labels from recent jobs with their usage counts"""
        return (
            JobStatsLabel.objects.filter_for_user(user)
            .filter(
                job_stats__started_at__gte=DateFilterOptions.PAST_MONTH.start_date,
            )
            .values("label")
            .annotate(count=Count("label"))
            .order_by("-count")
        )

    def initialize_label_multipliers(self, cost_config, labels):
        """Create multipliers for labels if they don't exist"""
        existing_multipliers = set(
            RunnerLabelMultiplier.objects.filter(
                cost_config=cost_config, label__in=labels
            ).values_list("label", flat=True)
        )

        # Create missing multipliers
        new_multipliers = [
            RunnerLabelMultiplier(cost_config=cost_config, label=label)
            for label in labels
            if label not in existing_multipliers
        ]
        if new_multipliers:
            RunnerLabelMultiplier.objects.bulk_create(new_multipliers)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_owner()
        cost_config = user.runner_cost_config

        # Get labels with their counts
        labels_data = self.get_labels_with_counts(user)
        if not labels_data:
            context["formset"] = None
            return context

        # Extract just the labels for multiplier creation
        labels = [item["label"] for item in labels_data]
        self.initialize_label_multipliers(cost_config, labels)

        # Create formset for existing multipliers
        MultiplierFormSet = modelformset_factory(
            RunnerLabelMultiplier,
            form=LabelMultiplierForm,
            formset=BaseLabelMultiplierFormSet,
            extra=0,
        )

        # Get multipliers ordered by usage count
        multipliers = RunnerLabelMultiplier.objects.filter(
            cost_config=cost_config, label__in=labels
        )

        # Create a mapping of labels to their counts
        label_counts = {item["label"]: item["count"] for item in labels_data}

        formset = MultiplierFormSet(queryset=multipliers)

        # Add count to each form
        for form in formset:
            form.label_count = label_counts.get(form.instance.label, 0)

        # Sort formset by label count
        formset.forms.sort(key=lambda f: f.label_count, reverse=True)

        context["formset"] = formset
        return context

    def post(self, request, *args, **kwargs):
        cost_config = self.get_owner().runner_cost_config
        label = None
        per_minute_rate = None
        for key, value in request.POST.items():
            if key.endswith("per_minute_rate"):
                per_minute_rate = value
            if key.endswith("label"):
                label = value
        try:
            multiplier = RunnerLabelMultiplier.objects.get(
                cost_config=cost_config, label=label
            )
            multiplier.per_minute_rate = per_minute_rate
            multiplier.save()
            messages.success(request, f"Label '{label}' updated successfully!")
        except RunnerLabelMultiplier.DoesNotExist:
            messages.error(request, f"Label '{label}' not found!")
        except ValueError as e:
            messages.error(request, f"Invalid value provided: {str(e)}")

        return redirect(self.success_url)


class LabelManagementView(LoginRequiredMixin, BaseLabelManagementView):
    pass


class DemoLabelManagementView(BaseLabelManagementView):
    template_name = "actions_data/demo_label_management.html"

    def get_owner(self) -> User:
        return User.objects.get(username=settings.DEMO_USERNAME)

    def post(self, request, *args, **kwargs):
        pass
