from django.db import models

from accounts.models import TrainerAccount
from clients.models import Client

class AIDraftPlan(models.Model):
    trainer_account = models.ForeignKey(
        TrainerAccount,
        on_delete=models.CASCADE,
        related_name="ai_draft_plans",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="ai_draft_plans",
    )
    program_length_weeks = models.PositiveIntegerField(default=4)
    session_duration_min = models.PositiveIntegerField(default=45)
    extra_instructions = models.TextField(blank=True)
    trainer_notes = models.TextField(blank=True, help_text="Trainer's edits before accepting")

    draft_json = models.JSONField(default=dict, blank=True)
    raw_summary = models.TextField(blank=True, help_text="Plain-text summary the LLM returned")
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_plan = models.ForeignKey(
        "plans.TrainingPlan",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_drafts",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AI draft for {self.client.full_name} @ {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def days(self) -> list[dict]:
        if not isinstance(self.draft_json, dict):
            return []
        return self.draft_json.get("days") or []
