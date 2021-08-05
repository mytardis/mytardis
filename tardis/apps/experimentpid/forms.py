import logging

from django import forms

from tardis.tardis_portal.forms import ExperimentForm

logger = logging.getLogger(__name__)


class ExperimentPIDForm(ExperimentForm):

    pid = forms.CharField(max_length=400, required=False)
