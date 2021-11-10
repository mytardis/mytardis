import logging
import re

from django import forms

from tardis.tardis_portal.forms import DatasetForm

logger = logging.getLogger(__name__)


class DatasetPIDForm(DatasetForm):

    pid = forms.CharField(max_length=400, required=False)
    alternative = forms.CharField(widget=forms.Textarea)

    def clean_alternative(self):
        rawdata = self.cleaned_data["alternative"]
        cleaned_alternative = []
        rawdata = re.split(",|;|\n", rawdata)
        for identifier in rawdata:
            cleaned_alternative.append(identifier.strip())
        return cleaned_alternative
