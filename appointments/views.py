from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.decorators import tenant_qs, trainer_required

from .forms import AppointmentForm
from .models import Appointment

def _hx_redirect(url):
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response

@trainer_required
def calendar(request):
    form = AppointmentForm(trainer_account=request.trainer_account)
    appointments = tenant_qs(Appointment, request).select_related("client").order_by("start_at")
    return render(request, "appointments/calendar.html", {
        "form": form,
        "appointments": appointments[:50],
        "session_types": Appointment.SESSION_TYPE_CHOICES,
        "statuses": Appointment.STATUS_CHOICES,
        "active_nav": "appointments",
    })

@trainer_required
def events_feed(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    qs = tenant_qs(Appointment, request).select_related("client")
    if start:
        try:
            qs = qs.filter(end_at__gte=parse_datetime(start) or datetime.fromisoformat(start))
        except (TypeError, ValueError):
            pass
    if end:
        try:
            qs = qs.filter(start_at__lte=parse_datetime(end) or datetime.fromisoformat(end))
        except (TypeError, ValueError):
            pass

    events = [
        {
            "id": a.pk,
            "title": f"{a.client.full_name} · {a.get_session_type_display()}",
            "start": a.start_at.isoformat(),
            "end": a.end_at.isoformat(),
            "classNames": [f"event-{a.colour_token}"],
            "extendedProps": {
                "status": a.status,
                "session_type": a.session_type,
                "notes": a.notes,
            },
        }
        for a in qs
    ]
    return JsonResponse(events, safe=False)

def _iso_for_input(value):
    if not value:
        return ""
    if hasattr(value, "strftime"):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%Y-%m-%dT%H:%M")
    return str(value)[:16]

@trainer_required
def appointment_create(request):
    initial_start = request.GET.get("start") or ""
    initial_end = request.GET.get("end") or ""

    if request.method == "POST":
        form = AppointmentForm(request.POST, trainer_account=request.trainer_account)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.trainer_account = request.trainer_account
            appt.save()
            messages.success(request, "Appointment scheduled.")
            target = reverse("appointments:calendar")
            return _hx_redirect(target) if request.htmx else redirect(target)
        start_value = _iso_for_input(form["start_at"].value())
        end_value = _iso_for_input(form["end_at"].value())
    else:
        initial = {}
        if initial_start:
            initial["start_at"] = initial_start
        if initial_end:
            initial["end_at"] = initial_end
        form = AppointmentForm(initial=initial, trainer_account=request.trainer_account)
        start_value = initial_start
        end_value = initial_end

    template = "appointments/appointment_modal.html" if request.htmx else "appointments/form.html"
    return render(request, template, {
        "form": form,
        "title": "New Appointment",
        "start_value": start_value,
        "end_value": end_value,
        "active_nav": "appointments",
    })

@trainer_required
def appointment_edit(request, pk):
    appt = get_object_or_404(tenant_qs(Appointment, request), pk=pk)
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appt, trainer_account=request.trainer_account)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated.")
            target = reverse("appointments:calendar")
            return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = AppointmentForm(instance=appt, trainer_account=request.trainer_account)
    template = "appointments/appointment_modal.html" if request.htmx else "appointments/form.html"
    return render(request, template, {
        "form": form,
        "appointment": appt,
        "title": "Edit Appointment",
        "start_value": _iso_for_input(appt.start_at),
        "end_value": _iso_for_input(appt.end_at),
        "active_nav": "appointments",
    })

@trainer_required
def appointment_delete(request, pk):
    appt = get_object_or_404(tenant_qs(Appointment, request), pk=pk)
    if request.method != "POST":
        return HttpResponse(status=405)
    appt.delete()
    messages.success(request, "Appointment deleted.")
    return redirect("appointments:calendar")
