from django.urls import path

from . import views

app_name = "progress"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("client/<int:client_id>/", views.client_progress, name="client"),
    path("client/<int:client_id>/chart-data/", views.chart_data, name="chart_data"),
    path("client/<int:client_id>/log/", views.log_create, name="log_create"),
    path("log/<int:pk>/delete/", views.log_delete, name="log_delete"),
]
