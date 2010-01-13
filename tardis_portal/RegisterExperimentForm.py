from django import forms

class RegisterExperimentForm(forms.Form):
	url = forms.CharField(max_length=400, label='METS XML url')
	private_password = forms.CharField(label="Private Password", \
	required=False) 
	ftp_location = forms.CharField(max_length=400, required=False)
	ftp_port = forms.IntegerField(max_value=65535, min_value=0, required=False)
	ftp_username = forms.CharField(max_length=50, required=False)
	ftp_password = forms.CharField(max_length=50, required=False)