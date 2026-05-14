from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clients.models import Client
from core.decorators import tenant_qs, trainer_required
from exercises.models import Exercise
from plans.models import TrainingPlan, TrainingPlanExercise

from .models import AIDraftPlan
from .services import generate_plan_draft

PLAN_MONTHLY_LIMITS = {
    "free": 3,
    "standard": 15,
    "pro": None,
}

def _ai_quota(request):
    plan = request.trainer_account.current_plan
    limit = PLAN_MONTHLY_LIMITS.get(plan, PLAN_MONTHLY_LIMITS["free"])
    if limit is None:
        return {"plan": plan, "limit": None, "used": 0, "remaining": None, "exhausted": False}
    now = timezone.localtime()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    used = AIDraftPlan.objects.filter(
        trainer_account=request.trainer_account,
        created_at__gte=month_start,
    ).count()
    remaining = max(0, limit - used)
    return {
        "plan": plan,
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "exhausted": remaining == 0,
    }

def _render_panel(request, *, client, draft, error=None, quota=None):
    return render(request, "genai/draft_panel.html", {
        "client": client,
        "draft": draft,
        "error": error,
        "quota": quota or _ai_quota(request),
    })

@trainer_required
def assistant(request):
    clients = (
        tenant_qs(Client, request)
        .filter(archived_at__isnull=True)
        .order_by("full_name")
    )
    selected_id = request.GET.get("client")
    client = None
    draft = None
    if selected_id:
        client = get_object_or_404(clients, pk=selected_id)
        draft = (
            AIDraftPlan.objects.filter(client=client, trainer_account=request.trainer_account)
            .order_by("-created_at")
            .first()
        )
    elif clients.exists():
        client = clients.first()
        draft = (
            AIDraftPlan.objects.filter(client=client, trainer_account=request.trainer_account)
            .order_by("-created_at")
            .first()
        )
    return render(request, "genai/assistant.html", {
        "clients": clients,
        "client": client,
        "draft": draft,
        "quota": _ai_quota(request),
        "active_nav": "genai",
    })

@trainer_required
def assistant_for_client(request, client_id):
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)
    return redirect(f"{request.build_absolute_uri('/ai/')}?client={client.pk}")

@trainer_required
def generate_draft(request, client_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)

    quota = _ai_quota(request)
    if quota["exhausted"]:
        msg = (
            f"You've used your {quota['limit']} AI drafts for this month on the {quota['plan'].title()} plan. "
            "Upgrade for more drafts."
        )
        return _render_panel(request, client=client, draft=None, error=msg, quota=quota)

    try:
        weeks = int(request.POST.get("program_length_weeks", 4))
        duration = int(request.POST.get("session_duration_min", 45))
    except (TypeError, ValueError):
        weeks, duration = 4, 45
    weeks = max(1, min(12, weeks))
    duration = max(15, min(120, duration))
    extra = (request.POST.get("extra_instructions") or "").strip()

    library = tenant_qs(Exercise, request).filter(is_active=True).order_by("name")

    result = generate_plan_draft(
        client,
        library=library,
        program_length_weeks=weeks,
        session_duration_min=duration,
        extra_instructions=extra,
    )

    if "error" in result:
        return _render_panel(request, client=client, draft=None, error=result["error"], quota=quota)

    draft = AIDraftPlan.objects.create(
        trainer_account=request.trainer_account,
        client=client,
        program_length_weeks=weeks,
        session_duration_min=duration,
        extra_instructions=extra,
        draft_json=result,
        raw_summary=result.get("summary", ""),
    )
    return _render_panel(request, client=client, draft=draft)

@trainer_required
def update_notes(request, draft_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    draft = get_object_or_404(
        AIDraftPlan.objects.filter(trainer_account=request.trainer_account),
        pk=draft_id,
    )
    draft.trainer_notes = (request.POST.get("trainer_notes") or "").strip()
    draft.save(update_fields=["trainer_notes"])
    return HttpResponse(status=204)

@trainer_required
def accept_draft(request, draft_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    draft = get_object_or_404(
        AIDraftPlan.objects.filter(trainer_account=request.trainer_account),
        pk=draft_id,
    )

    plan = TrainingPlan.objects.create(
        trainer_account=request.trainer_account,
        client=draft.client,
        title=f"AI-drafted plan {timezone.now():%Y-%m-%d}",
        goal_summary=draft.raw_summary or draft.client.fitness_goal,
        status=TrainingPlan.STATUS_DRAFT,
    )

    order = 0
    for day in draft.days:
        day_label = day.get("day_label") or ""
        for ex in day.get("exercises", []):
            order += 1
            name = (ex.get("name") or "").strip()
            if not name:
                continue

            exercise = (
                Exercise.objects.filter(trainer_account=request.trainer_account, name__iexact=name).first()
            )
            if exercise is None:
                exercise = Exercise.objects.create(
                    trainer_account=request.trainer_account,
                    name=name,
                    category="other",
                    default_sets=int(ex.get("sets") or 3),
                    default_reps=_first_int(ex.get("reps")) or 10,
                )
            reps_value = _first_int(ex.get("reps")) or exercise.default_reps
            TrainingPlanExercise.objects.create(
                plan=plan,
                exercise=exercise,
                exercise_order=order,
                sets=int(ex.get("sets") or exercise.default_sets),
                reps=reps_value,
                notes=(f"{day_label} {ex.get('notes', '')}").strip(),
            )

    draft.accepted_at = timezone.now()
    draft.accepted_plan = plan
    draft.save(update_fields=["accepted_at", "accepted_plan"])

    messages.success(request, "Draft accepted, saved as a real training plan.")
    return redirect("clients:detail", pk=draft.client_id)

def _first_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = ""
    for ch in str(value):
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    try:
        return int(digits) if digits else None
    except ValueError:
        return None
