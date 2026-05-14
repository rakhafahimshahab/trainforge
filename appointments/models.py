from django.db import models

from accounts.models import TrainerAccount
from clients.models import Client

class Appointment(models.Model):
    SESSION_TRAINING = "training_session"
    SESSION_CONSULTATION = "consultation"
    SESSION_CHECKIN = "check_in"
    SESSION_TYPE_CHOICES = [
        (SESSION_TRAINING, "Training Session"),
        (SESSION_CONSULTATION, "Consultation"),
        (SESSION_CHECKIN, "Check-in"),
    ]

    STATUS_SCHEDULED = "scheduled"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    session_type = models.CharField(
        max_length=24,
        choices=SESSION_TYPE_CHOICES,
        default=SESSION_TRAINING,
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["trainer_account", "start_at"]),
            models.Index(fields=["client", "start_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.client.full_name} - {self.start_at:%Y-%m-%d %H:%M}"

    @property
    def colour_token(self) -> str:
        if self.status == self.STATUS_CANCELLED:
            return "cancelled"
        if self.session_type == self.SESSION_CONSULTATION:
            return "consultation"
        return "training"
