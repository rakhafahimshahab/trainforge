from django.urls import reverse

def _safe(name):
    try:
        return reverse(name)
    except Exception:
        return "#"

TRAINER_LINKS = [
    {"label": "Client Programs", "url_name": "clients:list", "key": "clients"},
    {"label": "Appointments", "url_name": "appointments:calendar", "key": "appointments"},
    {"label": "Progress", "url_name": "progress:overview", "key": "progress"},
    {"label": "AI Assistant", "url_name": "genai:assistant", "key": "genai"},
]
ADMIN_LINKS = [
    {"label": "Trainer Subscriptions", "url_name": "subscriptions:list", "key": "subscriptions"},
]

def nav(request):
    user = getattr(request, "user", None)
    role = None
    trainer_account = None
    if user and user.is_authenticated:
        profile = getattr(user, "profile", None)
        role = getattr(profile, "role", None)
        trainer_account = getattr(user, "trainer_account", None)

    if role == "admin":
        links_source = ADMIN_LINKS
    else:
        links_source = TRAINER_LINKS

    links = [
        {"label": item["label"], "url": _safe(item["url_name"]), "key": item["key"]}
        for item in links_source
    ]

    current_plan = None
    pending_upgrade = None
    if trainer_account is not None:
        current_plan = trainer_account.current_plan
        from subscriptions.models import UpgradeRequest
        pending_upgrade = (
            UpgradeRequest.objects
            .filter(trainer_account=trainer_account, status=UpgradeRequest.STATUS_PENDING)
            .order_by("-requested_at")
            .first()
        )

    return {
        "nav_role": role,
        "nav_links": links,
        "nav_trainer_account": trainer_account,
        "nav_current_plan": current_plan,
        "nav_pending_upgrade": pending_upgrade,
    }
