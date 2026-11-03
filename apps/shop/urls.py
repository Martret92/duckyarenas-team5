from django.urls import path
from . import views
app_name='shop'
urlpatterns=[path('',views.catalog,name='catalog'),path('buy/',views.buy,name='buy'),path('purchases/',views.history,name='history')]
