from django import forms

class ActionForm(forms.Form):
    action = forms.ChoiceField(choices=[(v,v) for v in ("create","xp","coins","specialization","outfit","equip","buy")])
    amount = forms.IntegerField(required=False,min_value=1,max_value=1000000)
    sex = forms.ChoiceField(required=False,choices=[("male","Masculino"),("female","Femenino")])
    code = forms.CharField(required=False,max_length=100)
    item_id = forms.IntegerField(required=False,min_value=1)
    quantity = forms.IntegerField(required=False,min_value=1,max_value=50)
