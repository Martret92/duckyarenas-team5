"""Session-owned fictitious games; PRG grants and explicit historical replay."""

from secrets import token_hex

from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.ecomotor.models import TargetCatalogVersion
from apps.ecomotor.target_catalog_validation import InvalidTargetCatalogError

from .catalog import DemoCatalogError
from .data import NAMES, CODES, OPTIONS, VERSION
from .forms import PersistentDemoForm
from .isolation import demo_connection
from .services import (DemoAccessError, DemoInputError, DemoConflictError, DemoIntegrityError,
    DemoTransactionError, DemoDatabaseError, create_demo_progress, grant_demo_target_xp,
    read_demo_progress, issue_demo_operation)


@never_cache
@require_http_methods(["GET", "POST"])
def home(request):
    context = {"version": VERSION}
    status = 200
    bound = None
    try:
        demo_connection()  # Before touching the lazy DB session, including its history.
        if request.GET:
            raise DemoInputError("La demo no acepta identificadores ni parámetros GET.")
        secret = request.session.get("demo_secret")
        pk = request.session.get("demo_progress")
        if request.method == "POST":
            actions = request.POST.getlist("action")
            action = actions[0] if len(actions) == 1 and actions[0] == "start" else "grant"
            bound = PersistentDemoForm(request.POST, action=action)
            if bound.is_valid():
                if action == "start":
                    secret = secret or token_hex(32)
                    progress = create_demo_progress(session_token=secret)
                    request.session["demo_secret"] = secret
                    request.session["demo_progress"] = progress.pk
                    for key in ("demo_operation", "demo_last", "demo_replay"):
                        request.session.pop(key, None)
                else:
                    if not secret or pk is None:
                        raise DemoAccessError("Inicia primero una partida de esta sesión.")
                    progress, _, _ = read_demo_progress(pk, session_token=secret)
                    result = grant_demo_target_xp(progress, amount=bound.cleaned_data["amount"],
                        operation_token=bound.cleaned_data["operation"], session_token=secret)
                    request.session["demo_last"] = {"operation": bound.cleaned_data["operation"],
                                                    "amount": result.amount}
                    request.session["demo_replay"] = result.replay
                    if request.session.get("demo_operation") == bound.cleaned_data["operation"]:
                        request.session.pop("demo_operation", None)
                return HttpResponseRedirect(reverse("persistent-demo"))
            status = 400
        if secret and pk is not None:
            progress, xp_events, evolutions = read_demo_progress(pk, session_token=secret)
            operation = request.session.get("demo_operation")
            if operation is None:
                operation = issue_demo_operation(progress, session_token=secret)
                request.session["demo_operation"] = operation
            context.update(progress=progress, xp_events=xp_events, evolutions=evolutions,
                           options=OPTIONS, unlocked=progress.current_level >= 8,
                           epochs=tuple({"name": name, "current": progress.current_epoch.code == code}
                                        for code, name in zip(CODES, NAMES)))
            context["grant_form"] = PersistentDemoForm(initial={"action": "grant", "operation": operation})
            last = request.session.get("demo_last")
            if last:
                context["replay_form"] = PersistentDemoForm(initial={"action": "grant", **last})
                context["was_replay"] = request.session.get("demo_replay", False)
        context["start_form"] = PersistentDemoForm(action="start", initial={"action": "start"})
        if bound is not None:
            context["errors"] = bound.errors
            if "amount" in bound.fields:
                context["grant_form"] = bound
    except DemoAccessError:
        context["unavailable"] = "Partida u operación no disponible para esta sesión. No se ha concedido XP."
        status = 403
    except (DemoConflictError, DemoIntegrityError):
        context["unavailable"] = "Conflicto de operación o historial incoherente. Sin cambios; no se repara."
        status = 409
    except DemoInputError as error:
        context["unavailable"] = str(error)
        status = 400
    except (ImproperlyConfigured, DatabaseError, DemoDatabaseError, DemoTransactionError,
            DemoCatalogError, InvalidTargetCatalogError, TargetCatalogVersion.DoesNotExist):
        context["unavailable"] = "Demo no disponible. Revisa la SQLite aislada, migrate y seed; no se ha confirmado esta operación."
        status = 503
    return render(request, "ecomotor_target_demo/home.html", context, status=status)
