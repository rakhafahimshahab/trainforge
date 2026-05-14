from django import forms

from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["client", "session_type", "start_at", "end_at", "status", "notes"]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Session notes"}),
        }

    def __init__(self, *args, trainer_account=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainer_account is not None:
            self.fields["client"].queryset = trainer_account.clients.filter(archived_at__isnull=True)

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_at")
        end = cleaned.get("end_at")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned
