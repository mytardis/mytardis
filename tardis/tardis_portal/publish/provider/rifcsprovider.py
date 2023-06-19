import re

from django.conf import settings


class RifCsProvider(object):

    def get_rifcs_context(self, experiment):
        c = dict()
        c['experiment'] = experiment
        c['description'] = experiment.description
        return c

    def get_template(self, experiment):
        return settings.RIFCS_TEMPLATE_DIR + "default.xml"

    def can_publish(self, experiment):
        return experiment.public_access != experiment.PUBLIC_ACCESS_NONE

    def _is_html_formatted(self, text):
        if re.search(r'<.*?>',text):
            return True
        return False

    def is_schema_valid(self, experiment):
        # No schema, so always valid
        return True
