from django import forms


class RegisterMetamanForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(max_length=30, required=True,
                               widget=forms.PasswordInput)
    metaman = forms.FileField(required=False)
    experiment_owner = forms.CharField(required=False)
    authors = forms.CharField(required=False)
    beamline = forms.CharField(max_length=10, required=True)
    epn = forms.CharField(max_length=30, required=True)
    institution_name = forms.CharField(max_length=400, required=True)
    title = forms.CharField(max_length=400, required=True)
    description = forms.CharField(required=False)
    url = forms.CharField(max_length=255, required=False)
    handle = forms.CharField(required=False)
    start_time = forms.DateTimeField(required=False)
    end_time = forms.DateTimeField(required=False)
    # holding sample information
    sample = forms.FileField(required=False)
    # file with mx autoprocessing data
    extra = forms.FileField(required=False)
    # should this data pushed out if other MyTARDIS sites are found?
    transfer = forms.BooleanField(required=False)


class FileTransferRequestForm(forms.Form):
    originid = forms.CharField(max_length=30, required=True)
    eid = forms.CharField(max_length=30, required=True)
    site_settings_url = forms.CharField(max_length=255, required=True)


class ImportParametersForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(max_length=30, required=True,
                               widget=forms.PasswordInput)
    parameter_file = forms.FileField(required=True)
