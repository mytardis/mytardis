from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.forms.widgets import TextInput, Widget


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


class Label(Widget):
    tag = "label"

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe(u'<%(tag)s%(attrs)s>%(value)s</%(tag)s>' %
                         {'attrs': flatatt(final_attrs),
                          'value': value,
                          'tag': self.tag})


class Span(Label):
    tag = "span"
