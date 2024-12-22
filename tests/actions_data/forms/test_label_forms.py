from django.contrib.auth import get_user_model
from django.test import TestCase
from django.forms import forms, modelformset_factory, HiddenInput

from actions_data.models import RunnerCostConfig, RunnerLabelMultiplier
from actions_data.forms import (
    LabelMultiplierForm,
    LabelMultiplierFormSet,
)


def create_user():
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="12345")


class LabelMultiplierFormTests(TestCase):

    @classmethod
    def setUp(self):
        self.user = create_user()
        self.config = self.user.runner_cost_config
        self.config.save()
        self.multiplier = RunnerLabelMultiplier.objects.create(
            cost_config=self.config,
            label="test-label",
            per_minute_rate=0.1,
        )

    def test_form_initialization_label_rates(self):
        """Test form initialization in LABEL_RATES mode"""
        form = LabelMultiplierForm(
            instance=self.multiplier,
        )
        self.assertNotIsInstance(form.fields["per_minute_rate"].widget, HiddenInput)

    def test_readonly_label(self):
        """Test that label field is readonly"""
        form = LabelMultiplierForm(instance=self.multiplier)
        self.assertTrue(form.fields["label"].widget.attrs.get("readonly"))

    def test_valid_operational_units_data(self):
        """Test form validation with valid data in OPERATIONAL_UNITS mode"""
        data = {
            "label": "test-label",
            "per_minute_rate": "0.0",
        }
        form = LabelMultiplierForm(
            data=data,
            instance=self.multiplier,
        )
        self.assertTrue(form.is_valid())

    def test_valid_label_rates_data(self):
        """Test form validation with valid data in LABEL_RATES mode"""
        data = {
            "label": "test-label",
            "per_minute_rate": "0.15",
        }
        form = LabelMultiplierForm(
            data=data,
            instance=self.multiplier,
        )
        self.assertTrue(form.is_valid())


class LabelMultiplierFormSetTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.config = RunnerCostConfig.objects.get(user=self.user)
        self.config.save()
        self.labels = ["label1", "label2", "label3"]
        self.multipliers = []

        for label in self.labels:
            multiplier = RunnerLabelMultiplier.objects.create(
                cost_config=self.config,
                label=label,
                per_minute_rate=0.1,
            )
            self.multipliers.append(multiplier)

    def create_formset(self):
        """Helper method to create a formset"""
        MultiplierFormSet = modelformset_factory(
            RunnerLabelMultiplier,
            form=LabelMultiplierForm,
            formset=LabelMultiplierFormSet,
            extra=0,
        )
        return MultiplierFormSet(
            queryset=RunnerLabelMultiplier.objects.filter(cost_config=self.config),
        )

    def test_formset_initialization(self):
        """Test formset initialization"""
        formset = self.create_formset()
        self.assertEqual(len(formset.forms), len(self.labels))
        self.assertTrue(
            all(
                form.fields["label"].widget.attrs.get("readonly")
                for form in formset.forms
            )
        )
