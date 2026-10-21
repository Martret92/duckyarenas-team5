"""Local demonstration: no player access, ORM, session writes or confirmation."""

from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .demo_forms import DEMO_BUDGET, DEMO_OPTIONS, TargetStatsDemoForm


@require_http_methods(["GET", "POST"])
@csrf_protect
def target_stats_demo(request):
    form = TargetStatsDemoForm(request.POST if request.method == "POST" else None)
    result = None
    status = 200
    if request.method == "POST":
        if form.is_valid():
            result = {
                "option_label": dict(DEMO_OPTIONS)[form.cleaned_data["option"]],
                "points_used": form.calculation.points_used,
                "points_remaining": form.calculation.points_remaining,
            }
        else:
            status = 400
    return render(request, "ecomotor/target_stats_demo.html", {
        "form": form, "result": result, "demo_budget": DEMO_BUDGET,
    }, status=status)
