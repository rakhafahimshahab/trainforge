from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.calendar, name="calendar"),
    path("feed/", views.events_feed, name="feed"),
    path("new/", views.appointment_create, name="create"),
    path("<int:pk>/edit/", views.appointment_edit, name="edit"),
    path("<int:pk>/delete/", views.appointment_delete, name="delete"),
]
