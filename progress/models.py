from django.db import models

from accounts.models import TrainerAccount
from clients.models import Client
from exercises.models import Exercise
from plans.models import TrainingPlanExercise

class ProgressLog(models.Model):
    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="progress_logs",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="progress_logs",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
        related_name="progress_logs",
    )

    plan_exercise = models.ForeignKey(
        TrainingPlanExercise,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="progress_logs",
    )
    log_date = models.DateField()
    actual_sets = models.PositiveIntegerField(default=0)
    actual_reps = models.PositiveIntegerField(default=0)
    actual_weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-log_date", "-created_at"]
        indexes = [
            models.Index(fields=["client", "exercise", "log_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.client.full_name} · {self.exercise.name} · {self.log_date}"
