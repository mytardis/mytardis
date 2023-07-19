import re

from django.conf import settings


class RifCsProvider(object):
    def get_rifcs_context(self, experiment):
        return {"experiment": experiment, "description": experiment.description}

    def get_template(self, experiment):
        return f"{settings.RIFCS_TEMPLATE_DIR}default.xml"

    def can_publish(self, experiment):
        return experiment.public_access != experiment.PUBLIC_ACCESS_NONE

    def _is_html_formatted(self, text):
        return bool(re.search(r"<.*?>", text))

    def is_schema_valid(self, experiment):
        # No schema, so always valid
        return True
