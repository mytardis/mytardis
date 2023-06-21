from django.forms.utils import flatatt
from django.forms.widgets import TextInput, Widget
from django.utils.safestring import mark_safe


class CommaSeparatedInput(TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, list):
            value = ", ".join(value)
        return super().render(name, value, attrs, renderer=None)

    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        return [v.strip(" ") for v in value.split(",")]


class Label(Widget):
    tag = "label"

    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        final_attrs = dict(self.attrs, name=name)
        if attrs:
            final_attrs.update(attrs)
        return mark_safe(
            "<%(tag)s%(attrs)s>%(value)s</%(tag)s>"
            % {"attrs": flatatt(final_attrs), "value": value, "tag": self.tag}
        )


class Span(Label):
    tag = "span"
