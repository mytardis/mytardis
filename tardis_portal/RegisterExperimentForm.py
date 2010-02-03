from django import forms

class RegisterExperimentForm(forms.Form):
	username = forms.CharField(max_length=400, required=True)
	password = forms.CharField(max_length=400, required=True)
	xmldata = forms.CharField(widget=forms.Textarea, required=True)
	experiment_owner = forms.CharField(max_length=400, required=False)