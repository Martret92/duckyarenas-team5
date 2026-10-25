from django.urls import path
from . import views
app_name = "team5_ui"
urlpatterns = [
    path("", views.page, {"section":"dashboard"}, name="dashboard"),
    *[path(f"{name}/", views.page, {"section":name}, name=name) for name in ("player","evolution","specialization","wardrobe","inventory","museum","shop","wallet","arena","rewards")],
    path("action/", views.action, name="action"),
]
