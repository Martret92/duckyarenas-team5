from django import forms


class PurchaseForm(forms.Form):
    """Accept quantity and a per-render idempotency key, never a price or user ID."""

    operation_key = forms.CharField(max_length=255, strip=True, widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, max_value=(2**31) - 1, initial=1)
