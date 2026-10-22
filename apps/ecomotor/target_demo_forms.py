"""Strict transport parsing. All arithmetic belongs to the existing pure APIs."""

import re

from django import forms

from . import target_stats_validation
from .target_demo_data import DEMO_BUDGET, EPOCH_NAMES, EPOCH_CODES, OPTIONS, STAT_LABELS
from .target_stats_validation import TARGET_STAT_CODES, InvalidTargetStatsError


class DemoNumber(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(strip=False, max_length=20, **kwargs)
        self.widget.attrs.update(inputmode="numeric", pattern="[0-9]+")

    def clean(self, value):
        value = super().clean(value)
        if re.fullmatch("[0-9]+", value) is None:
            raise forms.ValidationError("Usa solo dígitos ASCII del 0 al 9, sin espacios ni signos.")
        return int(value)


class TargetDemoForm(forms.Form):
    action = forms.ChoiceField(choices=tuple((s, s) for s in ("xp", "choose", "stats", "outfit", "reset")),
                               widget=forms.HiddenInput)
    state = forms.CharField(max_length=2048, strip=False, widget=forms.HiddenInput)

    def __init__(self, *args, action="xp", **kwargs):
        super().__init__(*args, **kwargs)
        self.calculation = None
        if action == "xp":
            self.fields["amount"] = DemoNumber(label="XP ficticia que quieres sumar", initial="100")
        elif action == "choose":
            self.fields["option"] = forms.ChoiceField(label="Opción para visualizar", choices=OPTIONS)
        elif action == "outfit":
            self.fields["outfit"] = forms.ChoiceField(label="Vestimenta conceptual", choices=tuple(zip(EPOCH_CODES, EPOCH_NAMES)))
        elif action == "stats":
            for code, label in zip(TARGET_STAT_CODES, STAT_LABELS):
                self.fields[code] = DemoNumber(label=f"{code} · {label}", initial="0")

    def clean(self):
        cleaned = super().clean()
        allowed = set(self.fields) | {"csrfmiddlewaretoken"}
        if not hasattr(self.data, "getlist") or set(self.data) - allowed:
            self.add_error(None, "La petición contiene campos no permitidos.")
        elif any(len(self.data.getlist(key)) != 1 for key in self.fields) or any(
                len(self.data.getlist(key)) > 1 for key in self.data):
            self.add_error(None, "Cada campo debe enviarse exactamente una vez.")
        if self.errors:
            return cleaned
        if cleaned["action"] == "xp" and cleaned["amount"] == 0:
            self.add_error("amount", "La cantidad debe ser estrictamente positiva.")
        if cleaned["action"] == "stats":
            try:
                self.calculation = target_stats_validation.validate_target_stats(
                    tuple((c, 0) for c in TARGET_STAT_CODES),
                    tuple((c, cleaned[c]) for c in TARGET_STAT_CODES), budget=DEMO_BUDGET)
            except InvalidTargetStatsError:
                self.add_error(None, "Reparto inválido: dispones de hasta 45 puntos provisionales.")
        return cleaned
