from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.decorators import tenant_qs, trainer_required
from exercises.models import Exercise
from plans.forms import TrainingPlanForm
from plans.models import TrainingPlan

from .forms import ClientForm
from .models import Client

def _hx_redirect(url):
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response

def _exercise_library(request):
    return tenant_qs(Exercise, request).filter(is_active=True).order_by("name")

def _client_program_context(request, selected_client=None):
    clients = tenant_qs(Client, request).filter(archived_at__isnull=True)
    q = (request.GET.get("q") or "").strip()
    if q:
        clients = clients.filter(Q(full_name__icontains=q) | Q(email__icontains=q))
    clients = list(clients)
    if selected_client is None and clients:
        selected_client = clients[0]

    plan = None
    if selected_client:
        plan = (
            tenant_qs(TrainingPlan, request)
            .filter(client=selected_client, archived_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
    plan_exercises = []
    if plan:
        plan_exercises = list(plan.plan_exercises.select_related("exercise").all())

    return {
        "clients": clients,
        "selected_client": selected_client,
        "search_q": q,
        "exercises": _exercise_library(request),
        "plan": plan,
        "plan_form": TrainingPlanForm(instance=plan) if plan else TrainingPlanForm(),
        "plan_exercises": plan_exercises,
        "active_nav": "clients",
    }

@trainer_required
def client_list(request):
    ctx = _client_program_context(request)
    return render(request, "clients/program_management.html", ctx)

@trainer_required
def client_detail(request, pk):
    client = get_object_or_404(tenant_qs(Client, request), pk=pk)
    ctx = _client_program_context(request, selected_client=client)
    return render(request, "clients/program_management.html", ctx)

@trainer_required
def client_panel(request, pk):
    client = get_object_or_404(tenant_qs(Client, request), pk=pk)
    if request.GET.get("ensure_plan") == "1":
        already = TrainingPlan.objects.filter(
            client=client,
            trainer_account=request.trainer_account,
            archived_at__isnull=True,
        ).exists()
        if not already:
            TrainingPlan.objects.create(
                trainer_account=request.trainer_account,
                client=client,
                title=f"{client.full_name} Training Plan",
                status=TrainingPlan.STATUS_DRAFT,
            )
    ctx = _client_program_context(request, selected_client=client)
    return render(request, "clients/program_main.html", ctx)

@trainer_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.trainer_account = request.trainer_account
            client.save()
            messages.success(request, f"Added {client.full_name}.")
            target = reverse("clients:detail", kwargs={"pk": client.pk})
            return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = ClientForm()
    template = "clients/client_modal.html" if request.htmx else "clients/client_form.html"
    return render(request, template, {
        "form": form,
        "title": "New Client",
        "active_nav": "clients",
    })

@trainer_required
def client_edit(request, pk):
    client = get_object_or_404(tenant_qs(Client, request), pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client updated.")
            target = reverse("clients:detail", kwargs={"pk": client.pk})
            return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = ClientForm(instance=client)
    template = "clients/client_modal.html" if request.htmx else "clients/client_form.html"
    return render(request, template, {
        "form": form,
        "client": client,
        "title": f"Edit {client.full_name}",
        "active_nav": "clients",
    })

@trainer_required
def client_archive(request, pk):
    client = get_object_or_404(tenant_qs(Client, request), pk=pk)
    if request.method == "GET" and request.GET.get("confirm") == "1" and request.htmx:
        return render(request, "core/confirm_modal.html", {
            "title": f"Archive {client.full_name}?",
            "body": (
                "Their records, plans, and progress logs will be kept but the client "
                "will be marked inactive. You can restore them later from the Django admin."
            ),
            "action_url": reverse("clients:archive", kwargs={"pk": client.pk}),
            "action_label": "Archive",
            "action_class": "btn-danger",
        })
    if request.method != "POST":
        return HttpResponse(status=405)
    client.archived_at = timezone.now()
    client.status = Client.STATUS_INACTIVE
    client.save(update_fields=["archived_at", "status"])
    messages.success(request, f"Archived {client.full_name}.")
    target = reverse("clients:list")
    return _hx_redirect(target) if request.htmx else redirect(target)
