from django import forms


class EquipmentSearchForm(forms.Form):

    key = forms.CharField(label='Short Name',
        max_length=30, required=False)
    description = forms.CharField(label='Description',
        required=False)
    make = forms.CharField(label='Make', max_length=60, required=False)
    model = forms.CharField(label='Model', max_length=60, required=False)
    type = forms.CharField(label='Type', max_length=60, required=False)
    serial = forms.CharField(label='Serial No', max_length=60, required=False)
