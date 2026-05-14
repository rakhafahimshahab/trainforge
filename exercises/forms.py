from django import forms

from .models import Exercise

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ["name", "category", "description", "default_sets", "default_reps"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2, "placeholder": "Cueing notes, setup, etc."}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Exercise name is required.")
        return name
