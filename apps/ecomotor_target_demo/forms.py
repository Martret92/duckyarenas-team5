import re

from django import forms

from .data import MAX_XP


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
