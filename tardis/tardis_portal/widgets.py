from django.forms.widgets import TextInput


class CommaSeparatedInput(TextInput):
    def render(self, name, value, attrs=None):
        if isinstance(value, list):
            value = ', '.join(value)
        return super(CommaSeparatedInput, self).render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        value = super(CommaSeparatedInput, self).value_from_datadict(data,
                                                                     files,
                                                                     name)
        return [v.strip(' ') for v in value.split(',')]
