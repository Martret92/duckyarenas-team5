"""Standalone local demo URLconf: no admin, Core or V1 routes."""

from django.urls import path

from .target_demo_views import target_demo

urlpatterns = [path("demo/objetivo/", target_demo, name="target-demo")]
