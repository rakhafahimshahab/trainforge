from django.db import models

from accounts.models import TrainerAccount

class ActiveClientManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(archived_at__isnull=True)

class Client(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_INACTIVE, "Inactive"),
    ]

    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="clients",
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    fitness_goal = models.TextField(blank=True)
    preferred_times = models.CharField(
        max_length=120,
        blank=True,
        help_text="Free-text e.g. 'Mon / Wed / Fri mornings'",
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active = ActiveClientManager()

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["trainer_account", "status"])]

    def __str__(self) -> str:
        return self.full_name

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
