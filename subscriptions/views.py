from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.decorators import admin_required, trainer_required

from .forms import SubscriptionForm
from .models import Subscription, UpgradeRequest

def _hx_redirect(url):
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response

@admin_required
def subscription_list(request):
    qs = (
        Subscription.objects
        .select_related("trainer_account", "trainer_account__owner", "trainer_account__owner__profile")
        .filter(trainer_account__owner__profile__role="trainer")
        .order_by("-start_date")
    )

    search = (request.GET.get("q") or "").strip()
    if search:
        qs = qs.filter(
            Q(trainer_account__business_name__icontains=search)
            | Q(trainer_account__owner__email__icontains=search)
            | Q(trainer_account__owner__profile__full_name__icontains=search)
        )

    plan_filter = (request.GET.get("plan") or "").strip()
    if plan_filter and plan_filter != "all":
        qs = qs.filter(plan=plan_filter)

    status_filter = (request.GET.get("status") or "").strip()
    if status_filter and status_filter != "all":
        today = timezone.now().date()
        if status_filter == Subscription.STATUS_ARCHIVED:
            qs = qs.filter(archived_at__isnull=False)
        elif status_filter == Subscription.STATUS_ACTIVE:
            qs = qs.filter(archived_at__isnull=True, end_date__gte=today)
        elif status_filter == Subscription.STATUS_EXPIRED:
            qs = qs.filter(archived_at__isnull=True, end_date__lt=today)

    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get("page"))

    pending_requests = (
        UpgradeRequest.objects
        .filter(status=UpgradeRequest.STATUS_PENDING)
        .select_related("trainer_account", "trainer_account__owner")
        .order_by("-requested_at")
    )

    return render(request, "subscriptions/list.html", {
        "page_obj": page,
        "subscriptions": page.object_list,
        "search_q": search,
        "plan_filter": plan_filter or "all",
        "status_filter": status_filter or "all",
        "plan_choices": Subscription.PLAN_CHOICES,
        "pending_requests": pending_requests,
        "active_nav": "subscriptions",
    })

@admin_required
def subscription_edit(request, pk):
    sub = get_object_or_404(Subscription, pk=pk)
    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=sub)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription updated.")
            target = reverse("subscriptions:list")
            return _hx_redirect(target) if request.htmx else redirect(target)
    else:
        form = SubscriptionForm(instance=sub)
    template = "subscriptions/subscription_modal.html" if request.htmx else "subscriptions/form.html"
    return render(request, template, {
        "form": form,
        "subscription": sub,
        "title": f"Edit subscription for {sub.trainer_account.trainer_name}",
        "active_nav": "subscriptions",
    })

@admin_required
def subscription_archive(request, pk):
    sub = get_object_or_404(Subscription, pk=pk)

    if request.method == "GET" and request.GET.get("confirm") == "1" and request.htmx:
        return render(request, "core/confirm_modal.html", {
            "title": "Restore subscription?" if sub.archived_at else "Archive subscription?",
            "body": (
                f"This will {'restore' if sub.archived_at else 'archive'} the subscription for "
                f"{sub.trainer_account.trainer_name}. Records are preserved either way."
            ),
            "action_url": reverse("subscriptions:archive", kwargs={"pk": sub.pk}),
            "action_label": "Restore" if sub.archived_at else "Archive",
            "action_class": "btn-primary" if sub.archived_at else "btn-danger",
        })

    if request.method != "POST":
        return HttpResponse(status=405)

    if sub.archived_at is None:
        sub.archived_at = timezone.now()
        sub.save(update_fields=["archived_at"])
        messages.success(request, f"Archived subscription for {sub.trainer_account.trainer_name}.")
    else:
        sub.archived_at = None
        sub.save(update_fields=["archived_at"])
        messages.success(request, f"Restored subscription for {sub.trainer_account.trainer_name}.")
    target = reverse("subscriptions:list")
    return _hx_redirect(target) if request.htmx else redirect(target)

@trainer_required
def upgrade(request):
    account = request.trainer_account
    current_sub = account.active_subscription()
    pending = (
        UpgradeRequest.objects
        .filter(trainer_account=account, status=UpgradeRequest.STATUS_PENDING)
        .order_by("-requested_at")
        .first()
    )

    if request.method == "POST":
        target_plan = request.POST.get("plan", Subscription.PLAN_PRO)
        note = (request.POST.get("note") or "").strip()
        if target_plan == (current_sub.plan if current_sub else Subscription.PLAN_STARTER):
            messages.info(request, "You're already on that plan.")
        elif pending:
            messages.info(request, "You already have a pending upgrade request. The admin will be in touch.")
        else:
            UpgradeRequest.objects.create(
                trainer_account=account,
                requested_plan=target_plan,
                note=note,
            )
            messages.success(request, "Upgrade request sent. An admin will review it shortly.")
        target = reverse("clients:list")
        return _hx_redirect(target) if request.htmx else redirect(target)

    return render(request, "subscriptions/upgrade_modal.html", {
        "current_plan": current_sub.plan if current_sub else Subscription.PLAN_STARTER,
        "pending": pending,
    })

@admin_required
def upgrade_resolve(request, pk):
    req = get_object_or_404(UpgradeRequest, pk=pk)
    action = request.GET.get("action") or request.POST.get("action")

    if request.method == "GET" and request.GET.get("confirm") == "1" and request.htmx:
        is_approve = action == "approve"
        return render(request, "core/confirm_modal.html", {
            "title": ("Approve upgrade?" if is_approve else "Decline upgrade?"),
            "body": (
                f"{req.trainer_account.trainer_name} requested {req.get_requested_plan_display()}. "
                + ("Approving will switch their plan immediately." if is_approve else "They'll stay on their current plan.")
            ),
            "action_url": reverse("subscriptions:upgrade_resolve", kwargs={"pk": req.pk}) + f"?action={action}",
            "action_label": "Approve" if is_approve else "Decline",
            "action_class": "btn-primary" if is_approve else "btn-danger",
        })

    if request.method != "POST" or req.status != UpgradeRequest.STATUS_PENDING:
        return HttpResponse(status=405 if request.method != "POST" else 409)

    from django.utils import timezone as _tz

    if action == "approve":
        sub = req.trainer_account.active_subscription()
        from datetime import date, timedelta
        today = date.today()
        if sub:
            sub.plan = req.requested_plan
            sub.archived_at = None
            sub.save(update_fields=["plan", "archived_at"])
        else:
            Subscription.objects.create(
                trainer_account=req.trainer_account,
                plan=req.requested_plan,
                start_date=today,
                end_date=today + timedelta(days=365),
            )
        req.status = UpgradeRequest.STATUS_APPROVED
        messages.success(request, f"Approved: {req.trainer_account.trainer_name} is now on {req.get_requested_plan_display()}.")
    else:
        req.status = UpgradeRequest.STATUS_DECLINED
        messages.success(request, f"Declined upgrade request from {req.trainer_account.trainer_name}.")

    req.resolved_at = _tz.now()
    req.resolved_by = request.user
    req.save(update_fields=["status", "resolved_at", "resolved_by"])

    target = reverse("subscriptions:list")
    return _hx_redirect(target) if request.htmx else redirect(target)
