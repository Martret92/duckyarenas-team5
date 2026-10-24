"""Session-owned fictitious games; PRG grants and explicit historical replay."""

from secrets import token_hex

from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.forms import HiddenInput
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from apps.bank.services import BankError, InvalidAmount, IdempotencyConflict, WalletNotProvisioned

from apps.ecomotor.models import TargetCatalogVersion
from apps.ecomotor.target_catalog_validation import InvalidTargetCatalogError

from .catalog import DemoCatalogError
from .data import NAMES, CODES, OPTIONS, OPTION_CHOICES, VERSION
from .forms import PersistentDemoForm, PlayableForm, RewardDemoForm, REWARD_HTTP_ACTIVITIES
from . import playable_services as playable
from . import reward_demo_services as rewards
from apps.ecomotor.reward_types import InvalidRewardRuleSetError, AmbiguousRewardRulesError
from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES, InvalidTargetStatsError
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
            # An unsuccessful attempt must not leave a previous confirmation
            # looking like the outcome of this request or the following GET.
            request.session.pop("reward_notice", None)
            actions = request.POST.getlist("action")
            action = actions[0] if len(actions) == 1 else "grant"
            bound = (RewardDemoForm(request.POST) if action == "reward" else
                     PlayableForm(request.POST, action=action, auto_id="invalid_%s") if action in playable.ACTIONS
                     else PersistentDemoForm(request.POST, action="start" if action == "start" else "grant"))
            if bound.is_valid():
                if action == "start":
                    secret = secret or token_hex(32)
                    progress = create_demo_progress(session_token=secret)
                    request.session["demo_secret"] = secret
                    request.session["demo_progress"] = progress.pk
                    for key in ("demo_operation", "demo_last", "demo_replay"):
                        request.session.pop(key, None)
                    request.session.pop("playable_last", None)
                    for key in ("reward_tokens", "reward_last", "reward_notice", "reward_confirmed_tokens"):
                        request.session.pop(key, None)
                elif action == "reward":
                    if not secret or pk is None:
                        raise DemoAccessError("Inicia primero una partida de esta sesión.")
                    progress, _, _ = read_demo_progress(pk, session_token=secret)
                    values = bound.cleaned_data
                    result = rewards.apply_demo_reward(progress, activity=values["activity"],
                        fact_token=values["fact_token"], session_token=secret)
                    request.session["reward_last"] = {"action": "reward", "activity": values["activity"], "fact_token": values["fact_token"]}
                    confirmed = dict(request.session.get("reward_confirmed_tokens", {}))
                    confirmed[str(result.event_id)] = request.session["reward_last"]
                    request.session["reward_confirmed_tokens"] = confirmed
                    request.session["reward_notice"] = ("Replay Rewards histórico: sin nuevas concesiones; no se ha vuelto a acreditar." if result.replay
                        else "APPLIED: HINT sintético entregado y registrado." if result.item is not None
                        else "APPLIED: +5 DuckyCoins ficticias confirmadas." if result.coin_amount
                        else f"APPLIED: +{result.xp_amount} XP sintéticas y recompensa confirmadas juntas." if result.status == "APPLIED"
                        else "NO_REWARD: visita válida registrada, sin concesión de XP ni monedas ni objetos.")
                    tokens = dict(request.session.get("reward_tokens", {}))
                    if tokens.get(values["activity"]) == values["fact_token"]:
                        tokens.pop(values["activity"])
                    request.session["reward_tokens"] = tokens
                elif action in playable.ACTIONS:
                    if not secret or pk is None:
                        raise DemoAccessError("Inicia primero una partida de esta sesión.")
                    progress, _, _ = read_demo_progress(pk, session_token=secret)
                    values = bound.cleaned_data
                    arguments = {"option_code": values["option_code"], "operation_token": values["operation"],
                        "session_token": secret, "expected_revision": values["expected_revision"]}
                    if action != "switch":
                        arguments["increments"] = tuple((code, values[code]) for code in TARGET_STAT_CODES)
                    if action == "redistribute":
                        arguments["configuration_revision"] = values["configuration_revision"]
                    function = {"configure": playable.configure_demo_option, "switch": playable.switch_demo_option,
                                "redistribute": playable.redistribute_demo_option}[action]
                    result = function(progress, **arguments)
                    request.session["playable_notice"] = ("Replay jugable histórico: sin escrituras." if result.replay else
                        "Sin cambios: la revisión sigue vigente." if not result.changed else "Configuración jugable sintética guardada.")
                    if result.changed and action != "switch":
                        request.session["playable_last"] = request.POST.dict()
                        request.session["playable_last"].pop("csrfmiddlewaretoken", None)
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
            state, history = playable.read_demo_playable(progress, session_token=secret)
            context.update(playable_state=state, playable_history=history,
                           active_option_label=dict(OPTION_CHOICES).get(state.active_option),
                           playable_notice=request.session.get("playable_notice") if request.method == "GET" else None)
            if progress.current_level >= 8:
                def initial(kind, **extra):
                    return {"action": kind, "operation": playable.issue_playable_operation(progress, action=kind, session_token=secret),
                            "expected_revision": state.revision or "", **extra}
                context["configure_form"] = PlayableForm(initial=initial("configure"), auto_id="configure_%s")
                configured = {c.prepared.definition.option_code for c in state.configurations}
                context["configure_form"].fields["option_code"].choices = tuple(p for p in OPTION_CHOICES if p[0] not in configured)
                cards = []
                for config in state.configurations:
                    code = config.prepared.definition.option_code
                    cards.append({"config": config, "label": dict(OPTION_CHOICES)[code],
                        "rows": tuple((code, increment, effective) for (code, increment), (_, effective)
                                      in zip(config.prepared.calculation.increments, config.prepared.calculation.effective)),
                        "switch_form": PlayableForm(action="switch", auto_id=f"switch_{config.id}_%s", initial=initial("switch", option_code=code)),
                        "redistribute_form": PlayableForm(action="redistribute", initial=initial("redistribute",
                            option_code=code, configuration_revision=config.revision,
                            **dict(config.prepared.calculation.increments)), auto_id=f"redistribute_{config.id}_%s")})
                    for kind in ("switch_form", "redistribute_form"):
                        cards[-1][kind].fields["option_code"].widget = HiddenInput()
                context["configuration_cards"] = cards
            if request.session.get("playable_last"):
                saved = request.session["playable_last"]
                context["playable_replay_form"] = PlayableForm(action=saved["action"], initial=saved, auto_id="replay_%s")
            bank = rewards.read_demo_bank(progress, session_token=secret)
            context.update(bank=bank, reward_history=bank.rewards)
            context["inventory"] = rewards.read_demo_inventory(progress, session_token=secret)
            confirmed = request.session.get("reward_confirmed_tokens", {})
            context["reward_cards"] = tuple({"result": result, "replay": RewardDemoForm(
                initial=confirmed[str(result.event_id)], auto_id=f"reward_history_{result.event_id}_%s")
                if str(result.event_id) in confirmed else None} for result in bank.rewards)
            context["reward_notice"] = request.session.pop("reward_notice", None) if request.method == "GET" else None
            tokens = dict(request.session.get("reward_tokens", {}))
            missing = False
            reward_forms = []
            for activity, label in REWARD_HTTP_ACTIVITIES:
                if activity not in tokens:
                    tokens[activity] = rewards.issue_reward_fact(progress, activity=activity, session_token=secret)
                    missing = True
                reward_forms.append({"label": label, "form": RewardDemoForm(auto_id=f"reward_{activity}_%s",
                    initial={"action": "reward", "activity": activity, "fact_token": tokens[activity]})})
            if missing:
                request.session["reward_tokens"] = tokens
            context["reward_forms"] = reward_forms
            if request.session.get("reward_last"):
                context["reward_replay_form"] = RewardDemoForm(initial=request.session["reward_last"], auto_id="reward_replay_%s")
        context["start_form"] = PersistentDemoForm(action="start", initial={"action": "start"})
        if bound is not None:
            context["errors"] = bound.errors
            if "amount" in bound.fields:
                context["grant_form"] = bound
            elif isinstance(bound, PlayableForm):
                context["invalid_playable_form"] = bound
    except DemoAccessError:
        context["unavailable"] = "Partida u operación no disponible para esta sesión. Sin nuevas concesiones."
        status = 403
    except (DemoConflictError, DemoIntegrityError):
        context["unavailable"] = "Conflicto de operación o historial incoherente. Sin cambios; no se repara."
        status = 409
    except (IdempotencyConflict, WalletNotProvisioned):
        context["unavailable"] = "Conflicto o vinculación bancaria incoherente. Sin cambios; no se repara."
        status = 409
    except InvalidAmount:
        context["unavailable"] = "La operación bancaria no admite ese importe o saldo. Sin nueva concesión."
        status = 400
    except DemoInputError as error:
        context["unavailable"] = str(error)
        status = 400
    except InvalidTargetStatsError:
        context["unavailable"] = "Reparto inválido. Usa seis enteros no negativos y hasta 45 puntos provisionales. Sin cambios."
        status = 400
    except (ImproperlyConfigured, DatabaseError, DemoDatabaseError, DemoTransactionError,
            rewards.DemoRewardConfigurationError, InvalidRewardRuleSetError, AmbiguousRewardRulesError,
            DemoCatalogError, InvalidTargetCatalogError, TargetCatalogVersion.DoesNotExist, BankError):
        context["unavailable"] = "Demo no disponible. Revisa la SQLite aislada, migrate y seed; no se ha confirmado esta operación."
        status = 503
    return render(request, "ecomotor_target_demo/home.html", context, status=status)
