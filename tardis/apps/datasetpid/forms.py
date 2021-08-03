import logging

from django import forms
from django.forms import ModelForm
from django.db import transaction

from tardis_portal.forms import DatasetForm
from . import models


class DatasetPIDForm(forms.ModelForm):
    pid = forms.CharField()

    class Meta:
        model = models.DatasetPID
        fields = ["pid"]
