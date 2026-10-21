"""Strict HTTP input for an anonymous, nonpersistent demonstration only."""

import re

from django import forms

from . import target_stats_validation
from .target_stats_validation import (
    TARGET_STAT_CODES, InvalidTargetStatsNumericError,
    InvalidTargetStatsStructureError, TargetStatsBudgetExceededError,
)


DEMO_BUDGET = 45  # Internal provisional decision; never an official/global default.
DEMO_OPTIONS = (
    ("demo-developer", "Developer"), ("demo-ciber", "Ciber"),
    ("demo-sistemas", "Sistemas"), ("demo-data-ia", "Data IA"),
    ("demo-gamer", "Gamer"),
)
DEMO_LABELS = ("Ataque", "Defensa", "Velocidad", "Inteligencia", "Lógica", "Cuak")
MAX_HTTP_DIGITS = 10  # Transport guard, not an Ecomotor gameplay/storage limit.


class DemoIncrementField(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(strip=False, max_length=MAX_HTTP_DIGITS, **kwargs)
        self.widget.attrs.update({"inputmode": "numeric", "pattern": "[0-9]+"})

    def clean(self, value):
        text = super().clean(value)
        if re.fullmatch(r"[0-9]+", text) is None:
            raise forms.ValidationError("Introduce un entero no negativo con dígitos del 0 al 9.")
        return int(text)


class TargetStatsDemoForm(forms.Form):
    option = forms.ChoiceField(label="Opción tecnológica de demostración", choices=DEMO_OPTIONS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculation = None
        for code, label in zip(TARGET_STAT_CODES, DEMO_LABELS):
            self.fields[code] = DemoIncrementField(label=f"{code} · {label}", initial="0")

    def clean(self):
        cleaned = super().clean()
        allowed = {"option", *TARGET_STAT_CODES, "csrfmiddlewaretoken"}
        if set(self.data) - allowed:
            self.add_error(None, "La petición contiene campos no permitidos.")
        # Bound HTTP data must preserve multiplicity; never silently select a value.
        if not hasattr(self.data, "getlist"):
            self.add_error(None, "Se requiere una petición con campos explícitos.")
        else:
            for name in allowed:
                count = len(self.data.getlist(name))
                if count > 1:
                    self.add_error(None, "Cada campo debe enviarse una sola vez.")
        if self.errors:
            return cleaned
        try:
            self.calculation = target_stats_validation.validate_target_stats(
                tuple((code, 0) for code in TARGET_STAT_CODES),
                tuple((code, cleaned[code]) for code in TARGET_STAT_CODES),
                budget=DEMO_BUDGET,
            )
        except TargetStatsBudgetExceededError:
            self.add_error(None, "El reparto supera los 45 puntos provisionales disponibles.")
        except (InvalidTargetStatsStructureError, InvalidTargetStatsNumericError):
            self.add_error(None, "El reparto no tiene una estructura o valores válidos.")
        return cleaned
