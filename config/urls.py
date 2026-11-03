from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('team5/', include('apps.duckies.team5_ui.urls')),
    path('duckies/', include('apps.duckies.urls')),
    path('ecomotor/', include('apps.ecomotor.urls')),
    path('bank/', include('apps.bank.urls')),
    path('shop/', include('apps.shop.urls')),
    path('', RedirectView.as_view(pattern_name='team5_ui:dashboard', permanent=False)),
]

# El módulo demo no se importa ni se registra en el servidor normal.
from django.conf import settings
if getattr(settings, "TEAM5_DEMO_ENABLED", False) and "apps.team5_demo.apps.Team5DemoConfig" in settings.INSTALLED_APPS:
    urlpatterns.append(path("team5/demo/", include("apps.team5_demo.urls")))
