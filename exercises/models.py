from django.db import models

from accounts.models import TrainerAccount

class Exercise(models.Model):
    CATEGORY_CHOICES = [
        ("upper_body", "Upper Body"),
        ("lower_body", "Lower Body"),
        ("back", "Back"),
        ("core", "Core"),
        ("cardio", "Cardio"),
        ("mobility", "Mobility"),
        ("other", "Other"),
    ]

    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="exercises",
    )
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=24, choices=CATEGORY_CHOICES, default="other")
    description = models.TextField(blank=True)
    default_sets = models.PositiveIntegerField(default=3)
    default_reps = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("trainer_account", "name")]

    def __str__(self) -> str:
        return self.name

    @property
    def default_display(self) -> str:
        return f"{self.default_sets} x {self.default_reps}"
