from django.urls import path

from .views import allocate_points_view, allocation_history_view, progress_view, xp_history_view

app_name = "ecomotor"

urlpatterns = [
    path("progress/", progress_view, name="progress"),
    path("allocate-points/", allocate_points_view, name="allocate-points"),
    path("allocation-history/", allocation_history_view, name="allocation-history"),
    path("xp-history/", xp_history_view, name="xp-history"),
]
