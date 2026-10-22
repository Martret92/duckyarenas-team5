from django.urls import path

from .views import home

urlpatterns = [path("demo/objetivo-persistente/", home, name="persistent-demo")]
