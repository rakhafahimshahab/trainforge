from django.conf import settings
from django.db import models

class TrainerAccount(models.Model):

    business_name = models.CharField(max_length=120)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trainer_account",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["business_name"]

    def __str__(self) -> str:
        return self.business_name

    @property
    def trainer_name(self) -> str:
        profile = getattr(self.owner, "profile", None)
        if profile and profile.full_name:
            return profile.full_name
        return self.owner.email or self.business_name

    def active_subscription(self):
        from subscriptions.models import Subscription
        sub = (
            self.subscriptions
            .filter(archived_at__isnull=True)
            .order_by("-start_date")
            .first()
        )
        if sub is None:
            return None
        return sub

    @property
    def current_plan(self) -> str:
        sub = self.active_subscription()
        return sub.plan if sub else "free"

class Profile(models.Model):
    ROLE_TRAINER = "trainer"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_TRAINER, "Trainer"),
        (ROLE_ADMIN, "Admin"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_TRAINER)
    full_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.email} ({self.get_role_display()})"

    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN

    @property
    def is_trainer(self) -> bool:
        return self.role == self.ROLE_TRAINER
