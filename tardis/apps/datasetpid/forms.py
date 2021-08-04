# import logging

from django import forms

# from django.db import transaction
from tardis.tardis_portal.models.instrument import Instrument


class DatasetPIDForm(forms.Form):
    description = forms.CharField(max_length=400, required=True)
    directory = forms.CharField(max_length=400, required=False)
    instrument = forms.ModelChoiceField(queryset=Instrument.objects.all())
    pid = forms.CharField(max_length=400, required=False)
