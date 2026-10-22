"""Anonymous read-only target demo; signed state is neither XP history nor authority."""

from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError, transaction
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from . import target_xp_preview
from .models import TargetCatalogVersion
from .target_catalog_persistence import validate_target_catalog_version
from .target_catalog_validation import InvalidTargetCatalogError
from .target_demo_data import (
    CATALOG_ID, CATALOG_VERSION, DEMO_BUDGET, EPOCH_CODES, EPOCH_NAMES,
    HISTORICAL_OPTIONS, OPTIONS, TECH_OPTIONS, THRESHOLDS, demo_database,
)
from .target_demo_forms import TargetDemoForm
from .target_progression import calculate_target_progression

SALT = "ecomotor.target-demo.v1"


def _state(token):
    if type(token) is not str or len(token) > 2048:
        raise ValueError("Estado de demo inválido.")
    value = signing.loads(token, salt=SALT, max_age=4 * 60 * 60)
    if (type(value) is not dict or set(value) != {"xp", "option", "outfit"}
            or type(value["xp"]) is not int or not 0 <= value["xp"] < 10**20
            or type(value["option"]) is not str or value["option"] not in ("", *dict(OPTIONS))
            or type(value["outfit"]) is not str or value["outfit"] not in ("", *EPOCH_CODES)):
        raise ValueError("Estado no válido.")
    return value


def _catalog(alias):
    # A short IMMEDIATE read before A1.1. No creation/fallback on HTTP requests.
    with transaction.atomic(using=alias):
        version = TargetCatalogVersion.objects.using(alias).get(catalog_id=CATALOG_ID, version=CATALOG_VERSION)
        snapshot = validate_target_catalog_version(version.pk, using=alias)
        if (tuple(row.minimum_xp for row in snapshot.levels) != THRESHOLDS
                or snapshot.ordered_epoch_codes != EPOCH_CODES):
            raise InvalidTargetCatalogError("El catálogo de demo no corresponde al ejercicio sintético.")
        return version.pk, snapshot


@never_cache
@require_http_methods(["GET", "POST"])
def target_demo(request):
    try:
        alias = demo_database()
    except ImproperlyConfigured as error:
        raise Http404("La demo requiere su entorno aislado y una base migrada.") from error
    payload = {"xp": 0, "option": "", "outfit": ""}
    bound = None
    calculation = None
    transition = None
    notice = ""
    status = 200
    try:
        pk, catalog = _catalog(alias)
        progression = calculate_target_progression(0, 0, catalog)
        if request.method == "POST":
            actions = request.POST.getlist("action")
            action = actions[0] if len(actions) == 1 and actions[0] in ("xp", "choose", "stats", "outfit", "reset") else "xp"
            bound = TargetDemoForm(request.POST, action=action)
            if bound.is_valid():
                try:
                    payload = _state(bound.cleaned_data["state"])
                    progression = calculate_target_progression(payload["xp"], payload["xp"], catalog)
                    if payload["option"] and not progression.choice_unlocked_after:
                        raise ValueError("La elección no está desbloqueada.")
                    if payload["outfit"] and payload["option"] not in dict(TECH_OPTIONS):
                        raise ValueError("La vestimenta anterior requiere una especialización visual.")
                    if action == "reset":
                        payload = {"xp": 0, "option": "", "outfit": ""}
                        progression = calculate_target_progression(0, 0, catalog)
                        notice = "Simulación reiniciada. No se ha eliminado ni modificado ningún perfil."
                    elif action == "xp":
                        amount = bound.cleaned_data["amount"]
                        if payload["xp"] + amount >= 10**20:
                            raise ValueError("La demo limita el transporte HTTP a 20 dígitos, no el Ecomotor.")
                        transition = target_xp_preview.preview_target_xp(
                            pk, using=alias, xp_before=payload["xp"], amount=amount).plan.progression
                        progression = transition
                        payload["xp"] = progression.xp_after
                        notice = "XP simulada; no se ha concedido XP real."
                    elif not progression.choice_unlocked_after:
                        raise ValueError("La elección y el reparto se desbloquean en el nivel 8.")
                    elif action == "choose":
                        payload["option"] = bound.cleaned_data["option"]
                        payload["outfit"] = ""
                        notice = "Opción visualizada. No se ha guardado ninguna elección."
                    elif not payload["option"]:
                        raise ValueError("Elige primero una opción para visualizarla.")
                    elif action == "stats":
                        calculation = bound.calculation
                        notice = "Reparto válido para esta opción de demostración. No se guardan puntos."
                    elif action == "outfit":
                        if payload["option"] not in dict(TECH_OPTIONS):
                            raise ValueError("Las vestimentas anteriores se visualizan tras elegir especialización.")
                        payload["outfit"] = bound.cleaned_data["outfit"]
                        notice = "Vestimenta conceptual visualizada; no es equipamiento real."
                except (signing.BadSignature, ValueError) as error:
                    bound.add_error(None, "Estado caducado o inválido; reinicia con el enlace de la cabecera."
                                    if isinstance(error, signing.BadSignature) else str(error))
            if bound.errors:
                status = 400
                # Recover only a valid signed state; malformed HTTP cannot change XP.
                try:
                    tokens = request.POST.getlist("state")
                    payload = _state(tokens[0]) if len(tokens) == 1 else {"xp": 0, "option": "", "outfit": ""}
                except (signing.BadSignature, ValueError):
                    payload = {"xp": 0, "option": "", "outfit": ""}
                progression = calculate_target_progression(payload["xp"], payload["xp"], catalog)
        elif request.GET:
            # This page has no client-selectable catalog/profile/state query API.
            raise ValueError("Abre la URL sin parámetros para comenzar.")
    except (DatabaseError, TargetCatalogVersion.DoesNotExist, InvalidTargetCatalogError,
            target_xp_preview.TargetXPPreviewTransactionError):
        return render(request, "ecomotor/target_demo.html", {
            "unavailable": "Demo no preparada o catálogo incompatible. Ejecuta migrate y seed_target_demo_catalog en el entorno aislado."
        }, status=503)
    except ValueError:
        return render(request, "ecomotor/target_demo.html", {"unavailable": "Petición inválida. Abre la demo sin parámetros."}, status=400)
    token = signing.dumps(payload, salt=SALT, compress=True)
    forms = {name: TargetDemoForm(initial={"action": name, "state": token}, action=name)
             for name in ("xp", "choose", "stats", "outfit", "reset")}
    forms["outfit"].initial["outfit"] = payload["outfit"] or progression.epoch_after_code
    if calculation is not None:
        forms["stats"].initial.update(dict(calculation.increments))
    if bound is not None and bound.errors:
        # Keep safely escaped submitted values, including on rejection.
        name = bound.data.get("action")
        if name in forms:
            bound.initial["state"] = token
            forms[name] = bound
    current_index = EPOCH_CODES.index(progression.epoch_after_code)
    outfit = payload["outfit"] or progression.epoch_after_code
    return render(request, "ecomotor/target_demo.html", {
        "forms": forms, "progression": progression, "transition": transition,
        "request_errors": bound.errors if bound is not None else None,
        "notice": notice, "calculation": calculation, "budget": DEMO_BUDGET,
        "epoch_name": EPOCH_NAMES[current_index], "epoch_index": current_index + 1,
        "epochs": tuple({"name": name, "number": n + 1, "xp": THRESHOLDS[n],
                         "current": n == current_index, "reached": n <= current_index}
                        for n, name in enumerate(EPOCH_NAMES)),
        "history_options": HISTORICAL_OPTIONS, "tech_options": TECH_OPTIONS,
        "option_name": dict(OPTIONS).get(payload["option"], "Todavía sin elección"),
        "selected": payload["option"], "show_outfits": payload["option"] in dict(TECH_OPTIONS),
        "outfit_name": dict(HISTORICAL_OPTIONS)[outfit],
        "outfit_number": EPOCH_CODES.index(outfit) + 1,
        "epoch_before_name": dict(HISTORICAL_OPTIONS)[progression.epoch_before_code],
        "epoch_after_name": dict(HISTORICAL_OPTIONS)[progression.epoch_after_code],
        "crossed_epochs": tuple(dict(HISTORICAL_OPTIONS)[c] for c in progression.crossed_epoch_codes),
        "catalog_version": CATALOG_VERSION,
    }, status=status)
