"""Adaptador HTTP local de lectura; la identidad siempre procede de Django."""

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from apps.users.models import UserProfileEcomotor

from .progress_queries import (
    InconsistentQueryStateError, InvalidQueryProfileError, ProgressQueryDatabaseError,
    get_progress_overview, list_progress_history,
)


@login_required
@require_safe
def progress_view(request):
    try:
        profile = UserProfileEcomotor.objects.get(user=request.user)
        overview = get_progress_overview(profile)
        history = list_progress_history(profile, limit=10)
    except (UserProfileEcomotor.DoesNotExist, InvalidQueryProfileError):
        return HttpResponse("Progreso no encontrado.", status=404, content_type="text/plain; charset=utf-8")
    except InconsistentQueryStateError:
        return HttpResponse("El progreso no puede consultarse en su estado actual.", status=409,
                            content_type="text/plain; charset=utf-8")
    except (DatabaseError, ProgressQueryDatabaseError):
        return HttpResponse("La consulta de progreso no está disponible temporalmente.", status=503,
                            content_type="text/plain; charset=utf-8")
    return render(request, "ecomotor/progress.html", {"overview": overview, "history": history})
