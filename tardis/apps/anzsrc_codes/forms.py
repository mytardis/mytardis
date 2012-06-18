from django.forms import Form, CharField, URLField

class FoRCodeForm(Form):

    uri = URLField(required=True, max_length=2000)
    code = CharField(required=True, max_length=10)
    name = CharField(required=True, max_length=100)
