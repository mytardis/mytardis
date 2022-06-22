from django import forms
from django.forms.models import ModelChoiceField

from .models import Project


class ProjectForm(forms.ModelForm):

    name = forms.CharField()

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "principal_investigator",
            # "url",
            "institution",
            # "embargo_until",
            # "start_time",
            # "end_time",
        ]
