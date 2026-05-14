from django.contrib import admin

from .models import Profile, TrainerAccount

@admin.register(TrainerAccount)
class TrainerAccountAdmin(admin.ModelAdmin):
    list_display = ("business_name", "owner", "created_at")
    search_fields = ("business_name", "owner__email")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "full_name")
