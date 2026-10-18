"""Adaptadores HTTP locales; la identidad siempre procede de Django."""

import re
import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connections
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_safe

from apps.users.models import UserProfileEcomotor

from .forms import StatAllocationForm
from .stat_allocation import (
    AllocationConflictError, AllocationDatabaseError, AllocationOverflowError,
    InconsistentAllocationStateError, IneligibleStageError, InsufficientPointsError,
    InvalidAllocationConfigurationError, InvalidAllocationKeyError,
    InvalidAllocationProfileError, InvalidAttributeError, InvalidPointsError, allocate_stat_points,
)
from .progress_queries import (
    InconsistentQueryStateError, InvalidQueryProfileError, ProgressQueryDatabaseError,
    get_progress_overview, list_progress_history,
    InvalidHistoryParametersError,
)
from .stat_allocation_queries import list_stat_allocation_history


@login_required
@require_safe
def allocation_history_view(request):
    try:
        profile = UserProfileEcomotor.objects.get(user=request.user)
        cursors = request.GET.getlist("before_id")
        before_id = None
        if cursors:
            maximum = connections[profile._state.db].ops.integer_field_range("BigAutoField")[1]
            value = cursors[0]
            if (len(cursors) != 1 or not 1 <= len(value) <= len(str(maximum))
                    or re.fullmatch(r"[0-9]+", value) is None):
                raise InvalidHistoryParametersError("Cursor inválido.")
            before_id = int(value)
            if not 1 <= before_id <= maximum:
                raise InvalidHistoryParametersError("Cursor fuera de rango.")
        history = list_stat_allocation_history(profile, limit=10, before_id=before_id)
    except (UserProfileEcomotor.DoesNotExist, InvalidQueryProfileError):
        return HttpResponse("Progreso no encontrado.", status=404, content_type="text/plain; charset=utf-8")
    except InvalidHistoryParametersError:
        return HttpResponse("El cursor del historial no es válido.", status=400,
                            content_type="text/plain; charset=utf-8")
    except InconsistentQueryStateError:
        return HttpResponse("El historial no puede consultarse en su estado actual.", status=409,
                            content_type="text/plain; charset=utf-8")
    except (DatabaseError, ProgressQueryDatabaseError):
        return HttpResponse("La consulta del historial no está disponible temporalmente.", status=503,
                            content_type="text/plain; charset=utf-8")
    return render(request, "ecomotor/allocation_history.html", {"history": history})


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


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def allocate_points_view(request):
    form = None
    overview = None
    status = 200
    error = None
    try:
        profile = UserProfileEcomotor.objects.get(user=request.user)
        if request.method == "GET":
            overview = get_progress_overview(profile)
            form = StatAllocationForm(using=profile._state.db, initial={
                "operation_key": secrets.token_urlsafe(32),
            })
        else:
            form = StatAllocationForm(request.POST, using=profile._state.db)
            if form.is_valid():
                result = allocate_stat_points(profile, **form.cleaned_data)
                if result.replayed:
                    messages.info(request, "La operación ya estaba registrada. No se ha realizado un segundo gasto.")
                else:
                    messages.success(request, "Asignación de puntos aplicada.")
                return redirect("ecomotor:allocate-points")
            status = 400
            error = "Revisa los datos del formulario."
    except (UserProfileEcomotor.DoesNotExist, InvalidAllocationProfileError, InvalidQueryProfileError):
        return HttpResponse("Progreso no encontrado.", status=404, content_type="text/plain; charset=utf-8")
    except (InvalidAttributeError, InvalidPointsError, InvalidAllocationKeyError):
        status, error = 400, "Los datos de asignación no son válidos."
    except (IneligibleStageError, InsufficientPointsError, AllocationConflictError,
            InconsistentAllocationStateError, InconsistentQueryStateError, AllocationOverflowError):
        status, error = 409, "La asignación no puede realizarse en el estado actual."
    except (InvalidAllocationConfigurationError, AllocationDatabaseError,
            ProgressQueryDatabaseError, DatabaseError):
        status, error = 503, "La asignación no está disponible temporalmente."
    return render(request, "ecomotor/allocate_points.html", {
        "form": form, "overview": overview, "error": error,
    }, status=status)
