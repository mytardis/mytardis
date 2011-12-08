from django import forms
from tardis.apps.hpctardis.models import ActivityRecord

class ActivitiesSelectForm(forms.Form):
    activities = forms.ModelMultipleChoiceField(queryset=ActivityRecord.objects.all())