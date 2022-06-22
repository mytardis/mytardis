from django import forms
from django.conf import settings
from django.contrib.auth.models import User

# from django.forms.models import ModelChoiceField

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

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.fields["principal_investigator"].queryset = User.objects.exclude(
            pk=settings.PUBLIC_USER_ID
        )
