from django import forms

from .models import TrainingPlan, TrainingPlanExercise

class TrainingPlanForm(forms.ModelForm):
    class Meta:
        model = TrainingPlan
        fields = ["title", "status", "goal_summary"]
        widgets = {
            "goal_summary": forms.Textarea(attrs={"rows": 2, "placeholder": "Optional summary of plan goals"}),
        }

class TrainingPlanExerciseForm(forms.ModelForm):
    class Meta:
        model = TrainingPlanExercise
        fields = ["exercise", "sets", "reps", "notes"]
        widgets = {
            "notes": forms.TextInput(attrs={"placeholder": "Cue / tempo notes"}),
        }
