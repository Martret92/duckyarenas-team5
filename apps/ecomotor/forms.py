"""Validación HTTP estructural; S7-A conserva elegibilidad y saldo reales."""

import re

from django import forms
from django.db import connections

from .models import STAT_ATTRIBUTES, StatAllocationEvent


class StatAllocationForm(forms.Form):
    attribute = forms.ChoiceField(label="Atributo", choices=tuple(zip(
        STAT_ATTRIBUTES, ("ATK", "DEF", "LOG", "SPE", "VEL", "INT"),
    )))
    points = forms.CharField(label="Puntos", strip=False, widget=forms.TextInput(attrs={"inputmode": "numeric"}))
    operation_key = forms.CharField(min_length=1, max_length=255, strip=False, widget=forms.HiddenInput)

    def __init__(self, *args, using="default", **kwargs):
        super().__init__(*args, **kwargs)
        field = StatAllocationEvent._meta.get_field("points_spent")
        self._upper = connections[using].ops.integer_field_range(field.get_internal_type())[1]
        # Campo persistente con rango técnico finito; comprobar antes de int().
        self.fields["points"].max_length = len(str(self._upper))
        self.fields["points"].widget.attrs["maxlength"] = self.fields["points"].max_length

    def clean_points(self):
        value = self.cleaned_data["points"]
        if len(value) > self.fields["points"].max_length or re.fullmatch(r"[0-9]+", value) is None:
            raise forms.ValidationError("Introduce una cantidad entera positiva válida.")
        number = int(value)
        if not 1 <= number <= self._upper:
            raise forms.ValidationError("Introduce una cantidad entera positiva válida.")
        return number
