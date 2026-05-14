from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.subscription_list, name="list"),
    path("<int:pk>/edit/", views.subscription_edit, name="edit"),
    path("<int:pk>/archive/", views.subscription_archive, name="archive"),
    path("upgrade/", views.upgrade, name="upgrade"),
    path("requests/<int:pk>/resolve/", views.upgrade_resolve, name="upgrade_resolve"),
]
