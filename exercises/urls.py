from django.urls import path

from . import views

app_name = "exercises"

urlpatterns = [
    path("", views.exercise_list, name="list"),
    path("new/", views.exercise_create, name="create"),
    path("<int:pk>/edit/", views.exercise_edit, name="edit"),
    path("<int:pk>/delete/", views.exercise_delete, name="delete"),
]
