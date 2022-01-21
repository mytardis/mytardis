from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):

    name = forms.CharField()

    class Meta:
        model = Project
        fields = [
            "created_by",
            "name",
            "raid",
            "description",
            "lead_researcher",
            "url",
            "institution",
            "embargo_until",
            "start_time",
            "end_time",
        ]
