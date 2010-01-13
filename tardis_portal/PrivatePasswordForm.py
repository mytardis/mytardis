from django import forms

class PrivatePasswordForm(forms.Form):
	private_password = forms.CharField(label="Private Password",widget=forms.PasswordInput(render_value=False), \
	required=True)