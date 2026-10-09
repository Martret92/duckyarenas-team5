from django.urls import path
from . import views

app_name = "duckies"
urlpatterns = [
    path("", views.my_ducky, name="my_ducky"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/<int:pk>/", views.item_detail, name="item_detail"),
    path("equipment/", views.equipment, name="equipment"),
    path("equipment/history/", views.equipment_history, name="equipment_history"),
    path("equipment/equip/<int:pk>/", views.equip, name="equip"),
    path("equipment/unequip/<int:pk>/", views.unequip, name="unequip"),
]