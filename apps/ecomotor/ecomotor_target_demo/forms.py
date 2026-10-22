import re

from django import forms

from .data import MAX_XP
from .data import OPTION_CHOICES
from .reward_demo_rules import ACTIVITIES
from apps.ecomotor.target_stats_validation import TARGET_STAT_CODES


class PersistentDemoForm(forms.Form):
    action = forms.ChoiceField(choices=(("start", "start"), ("grant", "grant")), widget=forms.HiddenInput)

    def __init__(self, *args, action="grant", **kwargs):
        super().__init__(*args, **kwargs)
        if action == "grant":
            self.fields["operation"] = forms.CharField(max_length=1024, strip=False, widget=forms.HiddenInput)
            self.fields["amount"] = forms.CharField(label="XP sintética que quieres conceder", max_length=19,
                strip=False, initial="700", widget=forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]+"}))

    def clean(self):
        values = super().clean()
        if (not hasattr(self.data, "getlist") or set(self.data) - (set(self.fields) | {"csrfmiddlewaretoken"})
                or any(len(self.data.getlist(key)) != 1 for key in self.fields)
                or any(len(self.data.getlist(key)) > 1 for key in self.data)):
            self.add_error(None, "Campos inesperados, ausentes o duplicados.")
        if not self.errors and values["action"] == "grant":
            text = values.get("amount", "")
            if re.fullmatch("[0-9]+", text) is None or not 1 <= int(text) <= MAX_XP:
                self.add_error("amount", "Usa un entero positivo ASCII representable en SQLite, sin signos o espacios.")
            else:
                values["amount"] = int(text)
        return values


class PlayableForm(forms.Form):
    action = forms.ChoiceField(choices=tuple((a, a) for a in ("configure", "switch", "redistribute")), widget=forms.HiddenInput)
    operation = forms.CharField(max_length=1024, strip=False, widget=forms.HiddenInput)
    option_code = forms.ChoiceField(label="Opción jugable sintética", choices=OPTION_CHOICES)
    expected_revision = forms.CharField(required=False, max_length=19, strip=False, widget=forms.HiddenInput)

    def __init__(self, *args, action="configure", **kwargs):
        super().__init__(*args, **kwargs)
        self.kind = action
        if action == "redistribute":
            self.fields["configuration_revision"] = forms.CharField(max_length=19, strip=False, widget=forms.HiddenInput)
        if action != "switch":
            for code in TARGET_STAT_CODES:
                self.fields[code] = forms.CharField(label=code, max_length=19, strip=False, initial="0",
                    widget=forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]+"}))

    def clean(self):
        values = super().clean()
        if (not hasattr(self.data, "getlist") or set(self.data) - (set(self.fields) | {"csrfmiddlewaretoken"})
                or any(len(self.data.getlist(key)) != 1 for key in self.fields)
                or any(len(self.data.getlist(key)) > 1 for key in self.data)):
            self.add_error(None, "Campos inesperados, ausentes o duplicados.")
        if values.get("action") != self.kind:
            self.add_error(None, "Propósito de formulario incorrecto.")
        for key in ("expected_revision", "configuration_revision", *TARGET_STAT_CODES):
            if key not in self.fields or key not in values:
                continue
            text = values[key]
            if key == "expected_revision" and text == "" and self.kind == "configure":
                values[key] = None
            elif re.fullmatch("[0-9]+", text) is None or not (0 if key in TARGET_STAT_CODES else 1) <= int(text) <= MAX_XP:
                self.add_error(key, "Usa un entero ASCII representable, sin espacios ni signos.")
            else:
                values[key] = int(text)
        return values


class RewardDemoForm(forms.Form):
    action = forms.ChoiceField(choices=(("reward", "reward"),), widget=forms.HiddenInput)
    activity = forms.ChoiceField(choices=ACTIVITIES, widget=forms.HiddenInput)
    fact_token = forms.CharField(max_length=1536, strip=False, widget=forms.HiddenInput)

    def clean(self):
        values = super().clean()
        if (not hasattr(self.data, "getlist") or set(self.data) - (set(self.fields) | {"csrfmiddlewaretoken"})
                or any(len(self.data.getlist(key)) != 1 for key in self.fields)
                or any(len(self.data.getlist(key)) > 1 for key in self.data)):
            self.add_error(None, "Campos Rewards inesperados, ausentes o duplicados.")
        return values
