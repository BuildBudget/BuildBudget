from django import forms

from actions_data.models import RunnerLabelMultiplier


class LabelMultiplierFormSet(forms.BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return

        for form in self.forms:
            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("per_minute_rate", 0) < 0:
                raise forms.ValidationError("Per-minute rates cannot be negative")


class LabelMultiplierForm(forms.ModelForm):
    label = forms.CharField(widget=forms.TextInput(attrs={"readonly": True}))

    class Meta:
        model = RunnerLabelMultiplier
        fields = ["label", "per_minute_rate"]
        widgets = {
            "per_minute_rate": forms.NumberInput(
                attrs={"step": "0.0001", "min": "0", "class": "form-control"}
            ),
        }
