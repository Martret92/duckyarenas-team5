from django.urls import path
from . import views
app_name = 'team5_demo'
urlpatterns = [path('action/', views.action, name='action')]
