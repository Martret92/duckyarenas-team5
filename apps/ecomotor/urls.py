from django.urls import path

from .views import progress_view

app_name = "ecomotor"

urlpatterns = [path("progress/", progress_view, name="progress")]
