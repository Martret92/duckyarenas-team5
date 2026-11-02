from django.urls import path

from . import views

app_name = "shop"
urlpatterns = [
    path("", views.catalog_view, name="catalog"),
    path("purchases/", views.purchase_history_view, name="purchase-history"),
    path("<str:sku_code>/", views.product_detail_view, name="detail"),
    path("<str:sku_code>/purchase/", views.purchase_view, name="purchase"),
]
