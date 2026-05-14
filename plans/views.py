from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from clients.models import Client
from core.decorators import tenant_qs, trainer_required
from exercises.models import Exercise

from .forms import TrainingPlanForm
from .models import TrainingPlan, TrainingPlanExercise

def _hx_redirect(url):
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response

def _render_plan_panel(request, plan):
    exercises = tenant_qs(Exercise, request).filter(is_active=True).order_by("name")
    return render(request, "plans/plan_builder.html", {
        "plan": plan,
        "plan_form": TrainingPlanForm(instance=plan),
        "plan_exercises": plan.plan_exercises.select_related("exercise").all(),
        "exercises": exercises,
    })

@trainer_required
def plan_builder(request, client_id):
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)
    plan = (
        tenant_qs(TrainingPlan, request)
        .filter(client=client, archived_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if plan is None:
        plan = TrainingPlan.objects.create(
            trainer_account=request.trainer_account,
            client=client,
            title=f"{client.full_name} Training Plan",
            status=TrainingPlan.STATUS_DRAFT,
        )
    return _render_plan_panel(request, plan)

@trainer_required
def plan_save(request, client_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)
    plan = (
        tenant_qs(TrainingPlan, request)
        .filter(client=client, archived_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if plan is None:
        plan = TrainingPlan(trainer_account=request.trainer_account, client=client)
    form = TrainingPlanForm(request.POST, instance=plan)
    if form.is_valid():
        plan = form.save(commit=False)
        plan.trainer_account = request.trainer_account
        plan.client = client
        plan.save()
        if not request.htmx:
            messages.success(request, "Plan saved.")
            return redirect("clients:detail", pk=client.pk)
    return _render_plan_panel(request, plan)

@trainer_required
def plan_exercise_add(request, plan_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    plan = get_object_or_404(tenant_qs(TrainingPlan, request), pk=plan_id)
    exercise_id = request.POST.get("exercise_id")
    if not exercise_id:
        return HttpResponse(status=400)
    exercise = get_object_or_404(tenant_qs(Exercise, request), pk=exercise_id, is_active=True)
    next_order = (plan.plan_exercises.count() or 0) + 1
    TrainingPlanExercise.objects.create(
        plan=plan,
        exercise=exercise,
        exercise_order=next_order,
        sets=exercise.default_sets,
        reps=exercise.default_reps,
    )
    return _render_plan_panel(request, plan)

@trainer_required
def plan_exercise_update(request, pe_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    pe = get_object_or_404(
        TrainingPlanExercise.objects.select_related("plan"),
        pk=pe_id,
        plan__trainer_account=request.trainer_account,
    )
    updated_fields = []
    if "sets" in request.POST:
        try:
            pe.sets = max(0, int(request.POST["sets"] or 0))
            updated_fields.append("sets")
        except (TypeError, ValueError):
            pass
    if "reps" in request.POST:
        try:
            pe.reps = max(0, int(request.POST["reps"] or 0))
            updated_fields.append("reps")
        except (TypeError, ValueError):
            pass
    if "notes" in request.POST:
        pe.notes = (request.POST.get("notes") or "")[:240]
        updated_fields.append("notes")
    if updated_fields:
        pe.save(update_fields=updated_fields)
    return HttpResponse(status=204)

@trainer_required
def plan_exercise_delete(request, pe_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    pe = get_object_or_404(
        TrainingPlanExercise.objects.select_related("plan"),
        pk=pe_id,
        plan__trainer_account=request.trainer_account,
    )
    plan = pe.plan
    pe.delete()
    return _render_plan_panel(request, plan)

@trainer_required
def plan_delete(request, plan_id):
    plan = get_object_or_404(tenant_qs(TrainingPlan, request), pk=plan_id)
    if request.method == "GET" and request.GET.get("confirm") == "1" and request.htmx:
        return render(request, "core/confirm_modal.html", {
            "title": "Archive this plan?",
            "body": "The plan stays in the client's history but won't appear as their current plan.",
            "action_url": reverse("plans:delete", kwargs={"plan_id": plan.pk}),
            "action_label": "Archive",
            "action_class": "btn-danger",
        })
    if request.method != "POST":
        return HttpResponse(status=405)
    plan.archived_at = timezone.now()
    plan.save(update_fields=["archived_at"])
    messages.success(request, "Plan archived.")
    target = reverse("clients:detail", kwargs={"pk": plan.client_id})
    return _hx_redirect(target) if request.htmx else redirect(target)

@trainer_required
def plan_view(request, plan_id):
    plan = get_object_or_404(
        tenant_qs(TrainingPlan, request).select_related("client"),
        pk=plan_id,
    )
    return render(request, "plans/plan_view.html", {
        "plan": plan,
        "plan_exercises": plan.plan_exercises.select_related("exercise").order_by("exercise_order"),
        "active_nav": "clients",
    })
