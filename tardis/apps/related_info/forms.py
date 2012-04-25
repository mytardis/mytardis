from django.forms import Form, CharField, URLField, Select, Textarea

class RelatedInfoForm(Form):

    type = CharField( #@ReservedAssignment
                     widget=Select(choices=[('publication', 'Publication'),
                                            ('website', 'Website')]))
    identifier = URLField(required=True, max_length=2000)
    title = CharField(max_length=100, required=False)
    notes = CharField(required=False, widget=Textarea())
