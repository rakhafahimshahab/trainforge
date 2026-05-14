from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def trainer_required(view):

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if profile is None or not profile.is_trainer:
            return HttpResponseForbidden("Trainer access only.")
        trainer_account = getattr(request.user, "trainer_account", None)
        if trainer_account is None:
            return HttpResponseForbidden("Your trainer workspace is not set up.")
        request.trainer_account = trainer_account
        return view(request, *args, **kwargs)

    return wrapper

def admin_required(view):

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if profile is None or not profile.is_admin:
            return HttpResponseForbidden("Admin access only.")
        return view(request, *args, **kwargs)

    return wrapper

def role_redirect(request):
    profile = getattr(request.user, "profile", None)
    if profile and profile.is_admin:
        return redirect("subscriptions:list")
    return redirect("clients:list")

def tenant_qs(model, request):
    return model.objects.filter(trainer_account=request.trainer_account)
