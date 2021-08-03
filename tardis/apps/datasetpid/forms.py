import logging

from django import forms
from django.db import transaction
from tardis_portal.models.instrument import Instrument


class DatasetPIDForm(forms.Form):
    description = forms.TextField(required=True)
    directory = forms.TextField(required=False)
    instrument = forms.ModelChoiceField(queryset=Instrument.objects.all())
    pid = forms.TextField(required=False)
