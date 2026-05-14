from django.urls import path

from . import views

app_name = "genai"

urlpatterns = [
    path("", views.assistant, name="assistant"),
    path("client/<int:client_id>/", views.assistant_for_client, name="assistant_for_client"),
    path("client/<int:client_id>/generate/", views.generate_draft, name="generate"),
    path("draft/<int:draft_id>/edit-notes/", views.update_notes, name="update_notes"),
    path("draft/<int:draft_id>/accept/", views.accept_draft, name="accept"),
]
