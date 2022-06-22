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
            "url",
            "institution",
            "embargo_until",
            "start_time",
            "end_time",
        ]

    def is_valid(self):
        """
        Test the validity of the form, the form may be invalid even if the
        error attribute has no contents. This is because the returnd value
        is dependent on the validity of the nested forms.

        This validity also takes into account forign keys that might be
        dependent on an unsaved model.

        :return: validity
        :rtype: bool
        """
        if self.is_bound and bool(self.errors):
            return not bool(self.errors)

        # TODO since this is a compound field, this should merge the errors
        for ae in self.experiment_authors:
            for name, _ in ae.errors.items():
                if isinstance(ae.fields[name], ModelChoiceField):
                    continue
                if ae.is_bound and bool(ae.errors[name]):
                    return False
        return True
