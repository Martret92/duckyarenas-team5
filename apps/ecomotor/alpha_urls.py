"""Read-only V1 alpha; Core owns the external prefix and authentication mount."""

from django.urls import path

from .views import allocation_history_view, progress_view, xp_history_view

app_name = "ecomotor"

urlpatterns = [
    path("progress/", progress_view, {"alpha_mode": True}, name="progress"),
    path("xp-history/", xp_history_view, {"alpha_mode": True}, name="xp-history"),
    path("allocation-history/", allocation_history_view, {"alpha_mode": True}, name="allocation-history"),
]
