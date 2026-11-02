"""Formularios HTTP para Duckies; las reglas siguen en services.py."""
from django import forms

class OutfitSelectionForm(forms.Form):
    item_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)

class EquipItemForm(forms.Form):
    inventory_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
