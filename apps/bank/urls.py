from django.urls import path

from . import views

app_name = "bank"
urlpatterns = [
    path("wallet/", views.wallet_view, name="wallet"),
]
