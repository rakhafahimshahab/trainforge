from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import TrainerAccount

class Subscription(models.Model):
    PLAN_FREE = "free"
    PLAN_STANDARD = "standard"
    PLAN_PRO = "pro"
    PLAN_STARTER = "free"                                                                
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_STANDARD, "Standard"),
        (PLAN_PRO, "Pro"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_ARCHIVED = "archived"

    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.CharField(max_length=24, choices=PLAN_CHOICES, default=PLAN_STARTER)
    start_date = models.DateField()
    end_date = models.DateField()
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.trainer_account.business_name} - {self.get_plan_display()}"

    @property
    def status(self) -> str:
        if self.archived_at is not None:
            return self.STATUS_ARCHIVED
        if self.end_date < timezone.now().date():
            return self.STATUS_EXPIRED
        return self.STATUS_ACTIVE

    @property
    def status_label(self) -> str:
        return self.status.capitalize()

class UpgradeRequest(models.Model):

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_DECLINED = "declined"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DECLINED, "Declined"),
    ]

    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="upgrade_requests",
    )
    requested_plan = models.CharField(max_length=24, choices=Subscription.PLAN_CHOICES)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_upgrade_requests",
    )
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [models.Index(fields=["status", "requested_at"])]

    def __str__(self) -> str:
        return f"{self.trainer_account.trainer_name} -> {self.get_requested_plan_display()} ({self.status})"

    @property
    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING
