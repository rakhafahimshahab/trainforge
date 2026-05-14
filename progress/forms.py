from django import forms

from .models import ProgressLog

class ProgressLogForm(forms.ModelForm):
    class Meta:
        model = ProgressLog
        fields = ["exercise", "log_date", "actual_sets", "actual_reps", "actual_weight_kg", "notes"]
        widgets = {
            "log_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "How did the session go?"}),
        }

    def __init__(self, *args, trainer_account=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainer_account is not None:
            self.fields["exercise"].queryset = trainer_account.exercises.filter(is_active=True)
