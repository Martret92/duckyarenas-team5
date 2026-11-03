from django.urls import path
from . import views
app_name = 'team5_ui'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('action/', views.action, name='action'),
]
for slug in ('player','evolution','specialization','wardrobe','inventory','museum','shop','wallet','rewards','arena'):
    urlpatterns.append(path(slug+'/', views.dashboard, {'section': slug}, name=slug))
