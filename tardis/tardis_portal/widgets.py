from django.forms.widgets import MultiWidget, TextInput
from django.utils.safestring import mark_safe


class CommaSeparatedInput(TextInput):
    def render(self, name, value, attrs=None):
        if isinstance(value, list):
            value = ', '.join(value)
        return super(CommaSeparatedInput, self).render(name, value, attrs)


class MultiFileWidget(MultiWidget):
    def decompress(self, value):
        return value

    def render(self, name, value, attrs=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            output.append(widget.render(name, widget_value, final_attrs))
        return mark_safe(self.format_output(output))

    def value_from_datadict(self, data, files, name):
        return [widget.value_from_datadict(data, files, name)
                for i, widget in enumerate(self.widgets)]
