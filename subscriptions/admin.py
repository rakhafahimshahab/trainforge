from django.contrib import admin
from django.utils import timezone

from .models import Subscription

@admin.action(description="Archive selected subscriptions")
def archive(modeladmin, request, queryset):
    queryset.filter(archived_at__isnull=True).update(archived_at=timezone.now())

@admin.action(description="Restore selected subscriptions")
def restore(modeladmin, request, queryset):
    queryset.filter(archived_at__isnull=False).update(archived_at=None)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("trainer_account", "plan", "start_date", "end_date", "status_label", "archived_at")
    list_filter = ("plan", "archived_at")
    search_fields = ("trainer_account__business_name",)
    actions = [archive, restore]
    list_per_page = 25

    def has_delete_permission(self, request, obj=None):
        return False                
