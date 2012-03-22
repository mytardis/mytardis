from django import forms


class FileTransferRequestForm(forms.Form):
    uid = forms.CharField(max_length=30, required=True)
    dest_path = forms.CharField(max_length=300, required=True)
    site_settings_url = forms.CharField(max_length=255, required=True)


class ImportParametersForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(max_length=30, required=True,
                               widget=forms.PasswordInput)
    parameter_file = forms.FileField(required=True)
