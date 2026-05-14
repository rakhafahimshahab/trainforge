from django.urls import path

from . import views

app_name = "plans"

urlpatterns = [
    path("client/<int:client_id>/", views.plan_builder, name="builder"),
    path("client/<int:client_id>/save/", views.plan_save, name="save"),
    path("<int:plan_id>/exercise/add/", views.plan_exercise_add, name="exercise_add"),
    path("exercise/<int:pe_id>/update/", views.plan_exercise_update, name="exercise_update"),
    path("exercise/<int:pe_id>/delete/", views.plan_exercise_delete, name="exercise_delete"),
    path("<int:plan_id>/delete/", views.plan_delete, name="delete"),
    path("<int:plan_id>/view/", views.plan_view, name="view"),
]
