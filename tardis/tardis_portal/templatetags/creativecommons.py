from django.template import Library
from tardis.tardis_portal.models import \
    ExperimentParameter, Experiment
from tardis.tardis_portal.creativecommonshandler import CreativeCommonsHandler

register = Library()


def show_cc_license(value):
    """
    Shows creative commons license information for the experiment richly
    :param value: The experiment ID
    :type value: string
    :return: An html-formatted string of the creative commons license
    :rtype: string
    """
    experiment = Experiment.objects.get(id=value)
    cch = CreativeCommonsHandler(experiment_id=experiment.id, create=False)

    if not cch.has_cc_license():
        return "No license."
    else:
        psm = cch.get_or_create_cc_parameterset()

        image = ""
        try:
            image = psm.get_param('license_image', True)
        except ExperimentParameter.DoesNotExist:
            pass

        name = ""
        try:
            name = psm.get_param('license_name', True)
        except ExperimentParameter.DoesNotExist:
            pass

        uri = ""
        try:
            uri = psm.get_param('license_uri', True)
        except ExperimentParameter.DoesNotExist:
            pass

        if name == "":
            html = "No License."
        else:
            html = '<a href="' + uri + '"'\
            'rel="license" class="cc_js_a"><img width="88" height="31"'\
            ' border="0" class="cc_js_cc-button"'\
            'src="' + image + '"'\
            'alt="Creative Commons License"></a><br/>'\
            'This work is licensed under a <a rel="license"'\
            'href="' + uri + '">'\
            '' + name + '</a>.'

        return html

register.filter('show_cc_license', show_cc_license)
