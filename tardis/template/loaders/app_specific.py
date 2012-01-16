"""
Adapted from: http://djangosnippets.org/snippets/1376/
"""
from os.path import dirname, join, abspath, isdir

from django.db.models import get_app
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist
from django.template.loaders.filesystem import load_template_source
from django.template.loader import BaseLoader

class Loader(BaseLoader):
    is_usable = True

    def _get_template_vars(self, template_name):
        app_name, template_name = template_name.split(":", 1)
        try:
            template_dir = abspath(join(dirname(get_app(app_name).__file__), 'templates'))
        except ImproperlyConfigured:
            raise TemplateDoesNotExist()
        return template_name, template_dir

    def load_template_source(self, template_name, template_dirs=None):
        """
        Template loader that only serves templates from specific app's template directory.

        Works for template_names in format app_label:some/template/name.html
        """
        if ":" not in template_name:
            raise TemplateDoesNotExist()
        template_name, template_dir = self._get_template_vars(template_name)
        if not isdir(template_dir):
            raise TemplateDoesNotExist()
        return load_template_source(template_name, template_dirs=[template_dir])