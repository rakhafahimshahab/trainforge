from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("core.urls")),
    path("clients/", include("clients.urls")),
    path("exercises/", include("exercises.urls")),
    path("plans/", include("plans.urls")),
    path("appointments/", include("appointments.urls")),
    path("progress/", include("progress.urls")),
    path("subscriptions/", include("subscriptions.urls")),
    path("ai/", include("genai.urls")),
]
