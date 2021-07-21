from django import forms


def openid_user_migration_form():
    """Create a user migration form with username and password field.

    """

    fields = {}
    fields['username'] = forms.CharField(
        label='Username', max_length=75, required=True)
    fields['password'] = forms.CharField(
        required=True, widget=forms.PasswordInput(),
        label='Password')

    return type('openid_user_migration_form', (forms.BaseForm, ),
                {'base_fields': fields})
