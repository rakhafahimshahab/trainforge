from django.db import models

from accounts.models import TrainerAccount
from clients.models import Client
from exercises.models import Exercise

class TrainingPlan(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
    ]

    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="training_plans",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="training_plans",
    )
    title = models.CharField(max_length=160)
    goal_summary = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["trainer_account", "status"])]

    def __str__(self) -> str:
        return f"{self.title} - {self.client.full_name}"

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

class TrainingPlanExercise(models.Model):

    plan = models.ForeignKey(
        TrainingPlan,
        on_delete=models.CASCADE,
        related_name="plan_exercises",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT,
        related_name="plan_entries",
    )
    exercise_order = models.PositiveIntegerField(default=0)
    sets = models.PositiveIntegerField(default=3)
    reps = models.PositiveIntegerField(default=10)
    notes = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["exercise_order", "id"]

    def __str__(self) -> str:
        return f"{self.exercise.name} ({self.sets}x{self.reps})"
