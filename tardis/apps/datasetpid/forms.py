import logging

from django import forms

from tardis.tardis_portal.forms import DatasetForm

logger = logging.getLogger(__name__)


class DatasetPIDForm(DatasetForm):

    pid = forms.CharField(max_length=400, required=False)
