from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.decorators import tenant_qs, trainer_required

from .forms import ExerciseForm
from .models import Exercise

def _hx_redirect(url):
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response

@trainer_required
def exercise_list(request):
    exercises = tenant_qs(Exercise, request).order_by("name")
    return render(request, "exercises/list.html", {
        "exercises": exercises,
        "active_nav": "clients",
    })

@trainer_required
def exercise_create(request):
    if request.method == "POST":
        form = ExerciseForm(request.POST)
        if form.is_valid():
            exercise = form.save(commit=False)
            exercise.trainer_account = request.trainer_account
            try:
                exercise.save()
            except Exception:
                form.add_error("name", "You already have an exercise with this name.")
            else:
                messages.success(request, f"Added exercise: {exercise.name}.")
                target = request.POST.get("next") or reverse("exercises:list")
                return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = ExerciseForm()
    template = "exercises/exercise_modal.html" if request.htmx else "exercises/form.html"
    return render(request, template, {
        "form": form,
        "title": "New Exercise",
        "next": request.GET.get("next", ""),
        "active_nav": "clients",
    })

@trainer_required
def exercise_edit(request, pk):
    exercise = get_object_or_404(tenant_qs(Exercise, request), pk=pk)
    if request.method == "POST":
        form = ExerciseForm(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercise updated.")
            target = reverse("exercises:list")
            return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = ExerciseForm(instance=exercise)
    template = "exercises/exercise_modal.html" if request.htmx else "exercises/form.html"
    return render(request, template, {
        "form": form,
        "exercise": exercise,
        "title": f"Edit {exercise.name}",
        "active_nav": "clients",
    })

@trainer_required
def exercise_delete(request, pk):
    exercise = get_object_or_404(tenant_qs(Exercise, request), pk=pk)
    if request.method == "GET" and request.GET.get("confirm") == "1" and request.htmx:
        return render(request, "core/confirm_modal.html", {
            "title": f"Remove {exercise.name}?",
            "body": (
                "If this exercise is referenced by an existing plan or progress log, it will be "
                "hidden from the library instead of deleted, so your history stays intact."
            ),
            "action_url": reverse("exercises:delete", kwargs={"pk": exercise.pk}),
            "action_label": "Remove",
            "action_class": "btn-danger",
        })
    if request.method != "POST":
        return HttpResponse(status=405)
    if exercise.plan_entries.exists() or exercise.progress_logs.exists():
        exercise.is_active = False
        exercise.save(update_fields=["is_active"])
        messages.success(request, f"Hid {exercise.name} from the library (still referenced by past plans).")
    else:
        name = exercise.name
        exercise.delete()
        messages.success(request, f"Removed {name}.")
    target = reverse("exercises:list")
    return _hx_redirect(target) if request.htmx else redirect(target)
