from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
app_name = "duckies"
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="duckies/login.html", next_page="duckies:dashboard"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="duckies:login"), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("inventory/", views.inventory, name="inventory"),
    path("equipment/", views.equipment, name="equipment"),
    path("museum/", views.museum, name="museum"),
    path("setup/", views.setup, name="setup"),
    path("action/", views.action, name="action"),
]
