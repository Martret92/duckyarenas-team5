from django.urls import path
from . import views
app_name='bank'
urlpatterns=[path('',views.wallet,name='wallet'),path('transactions/',views.transactions,name='transactions')]
