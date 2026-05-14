from datetime import date, timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, TrainerAccount

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if not created:
        return
    Profile.objects.get_or_create(
        user=instance,
        defaults={
            "role": Profile.ROLE_TRAINER,
            "full_name": (instance.get_full_name() or "").strip() or instance.email or "",
        },
    )

    profile = instance.profile
    if profile.role == Profile.ROLE_TRAINER and not hasattr(instance, "trainer_account"):
        account = TrainerAccount.objects.create(
            owner=instance,
            business_name=profile.full_name or (instance.email.split("@")[0] if instance.email else "My Studio"),
        )

        from subscriptions.models import Subscription
        today = date.today()
        Subscription.objects.create(
            trainer_account=account,
            plan=Subscription.PLAN_FREE,
            start_date=today,
            end_date=today + timedelta(days=365 * 10),
        )
