from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from appointments.models import Appointment
from clients.models import Client
from core.decorators import tenant_qs, trainer_required

from .forms import ProgressLogForm
from .models import ProgressLog

def _hx_redirect(url):
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response

def _client_stats(request, client):
    appointments = tenant_qs(Appointment, request).filter(client=client)
    completed = appointments.filter(status=Appointment.STATUS_COMPLETED).count()
    total = appointments.exclude(status=Appointment.STATUS_SCHEDULED).count()
    adherence = round((completed / total) * 100) if total else 0
    return {
        "sessions_completed": completed,
        "adherence_rate": adherence,
    }

@trainer_required
def overview(request):
    clients = (
        tenant_qs(Client, request)
        .filter(archived_at__isnull=True)
        .annotate(latest_log=Max("progress_logs__log_date"), log_count=Count("progress_logs"))
        .order_by("full_name")
    )
    chosen_id = request.GET.get("client")
    if chosen_id:
        return redirect("progress:client", client_id=chosen_id)
    return render(request, "progress/overview.html", {
        "clients": clients,
        "active_nav": "progress",
    })

@trainer_required
def client_progress(request, client_id):
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)
    logs = (
        ProgressLog.objects.filter(client=client, trainer_account=request.trainer_account)
        .select_related("exercise")
        .order_by("-log_date", "-created_at")[:50]
    )
    stats = _client_stats(request, client)
    return render(request, "progress/client.html", {
        "client": client,
        "logs": logs,
        "stats": stats,
        "active_nav": "progress",
    })

@trainer_required
def chart_data(request, client_id):
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)
    logs = (
        ProgressLog.objects.filter(client=client, trainer_account=request.trainer_account)
        .exclude(actual_weight_kg__isnull=True)
        .select_related("exercise")
        .order_by("log_date")
    )

    by_exercise: dict[str, list[tuple[str, Decimal]]] = defaultdict(list)
    all_dates = set()
    for log in logs:
        date_str = log.log_date.isoformat()
        by_exercise[log.exercise.name].append((date_str, log.actual_weight_kg))
        all_dates.add(date_str)

    labels = sorted(all_dates)
    palette = ["#2ee66b", "#f5c451", "#5ad1ff", "#ff8fa3", "#b78bff", "#ffb86b"]
    datasets = []
    for idx, (name, points) in enumerate(sorted(by_exercise.items())):
        date_to_weight = {d: float(w) for d, w in points}
        datasets.append({
            "label": name,
            "data": [date_to_weight.get(d) for d in labels],
            "borderColor": palette[idx % len(palette)],
            "backgroundColor": palette[idx % len(palette)] + "33",
            "tension": 0.3,
            "spanGaps": True,
        })

    return JsonResponse({"labels": labels, "datasets": datasets})

@trainer_required
def log_create(request, client_id):
    client = get_object_or_404(tenant_qs(Client, request), pk=client_id)
    if request.method == "POST":
        form = ProgressLogForm(request.POST, trainer_account=request.trainer_account)
        if form.is_valid():
            log = form.save(commit=False)
            log.trainer_account = request.trainer_account
            log.client = client
            log.save()
            messages.success(request, "Progress entry added.")
            target = reverse("progress:client", kwargs={"client_id": client.pk})
            return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = ProgressLogForm(trainer_account=request.trainer_account)
    template = "progress/log_modal.html" if request.htmx else "progress/log_form.html"
    return render(request, template, {
        "form": form,
        "client": client,
        "title": f"Add Progress Entry for {client.full_name}",
        "active_nav": "progress",
    })

@trainer_required
def log_delete(request, pk):
    log = get_object_or_404(
        ProgressLog.objects.filter(trainer_account=request.trainer_account),
        pk=pk,
    )
    if request.method == "GET" and request.GET.get("confirm") == "1" and request.htmx:
        return render(request, "core/confirm_modal.html", {
            "title": "Delete progress entry?",
            "body": f"This will permanently remove the {log.exercise.name} log on {log.log_date}.",
            "action_url": reverse("progress:log_delete", kwargs={"pk": log.pk}),
            "action_label": "Delete",
            "action_class": "btn-danger",
        })
    if request.method != "POST":
        return HttpResponse(status=405)
    client_id = log.client_id
    log.delete()
    messages.success(request, "Entry removed.")
    target = reverse("progress:client", kwargs={"client_id": client_id})
    return _hx_redirect(target) if request.htmx else redirect(target)
