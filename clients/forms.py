from django import forms

from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["full_name", "email", "phone", "fitness_goal", "preferred_times", "status", "notes"]
        widgets = {
            "fitness_goal": forms.Textarea(attrs={"rows": 2, "placeholder": "e.g. Build strength, lose body fat"}),
            "preferred_times": forms.TextInput(attrs={"placeholder": "e.g. Mon / Wed / Fri mornings"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Any limitations or context"}),
        }

    def clean_full_name(self):
        name = (self.cleaned_data.get("full_name") or "").strip()
        if len(name) < 2:
            raise forms.ValidationError("Please enter the client's full name.")
        return name
