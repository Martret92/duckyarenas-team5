from django.urls import path
from . import views

app_name = 'duckies'
urlpatterns = [
    path('', views.detail_view, name='detail'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('outfits/', views.outfits_view, name='outfits'),
    path('museum/', views.museum_view, name='museum'),
    path('outfits/select/', views.select_outfit_view, name='select-outfit'),
    path('inventory/equip/', views.equip_view, name='equip'),
]
