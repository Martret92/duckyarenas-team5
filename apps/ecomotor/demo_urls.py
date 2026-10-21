"""Opt-in demonstration URLconf; deliberately excludes global/V1/admin routes."""

from django.urls import path

from .demo_views import target_stats_demo


urlpatterns = [path("demo/ecomotor/", target_stats_demo, name="target-stats-demo")]
