from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .decorators import role_redirect


def landing(request):
    return render(request, "landing.html")


@login_required
def dashboard(request):
    return role_redirect(request)
