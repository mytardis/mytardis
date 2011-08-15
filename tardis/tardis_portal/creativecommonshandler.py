'''

'''
from tardis.tardis_portal.ParameterSetManager import\
    ParameterSetManager
from tardis.tardis_portal.models import \
    Experiment, ExperimentParameterSet

"""
Creative Commons Handler

A wrapper for creative commons interactions on a ParameterSet

.. moduleauthor:: Steve Androulakis <steve.androulakis@monash.edu>

"""


class CreativeCommonsHandler():

    psm = None
    schema = "http://www.tardis.edu.au/schemas" +\
    "/creative_commons/2011/05/17"
    experiment_id = None

    def __init__(self, experiment_id=experiment_id, create=True):
        """
        :param experiment_id: The id of the experiment
        :type experiment_id: integer
        :param create: If true, creates a new parameterset object to
        hold the cc license
        :type create: boolean
        """

        self.experiment_id = experiment_id

        if create:
            self.psm = self.get_or_create_cc_parameterset(create=True)
        else:
            self.psm = self.get_or_create_cc_parameterset(create=False)

    def get_or_create_cc_parameterset(self, create=True):
        """
        Gets the creative commons parameterset for the experiment
        :param create: If true, creates a new parameterset object to
        hold the cc license if one doesn't exist
        :type create: boolean
        :return: The parameterset manager for the cc parameterset
        :rtype: :class:`tardis.tardis_portal.ParameterSetManager.
        ParameterSetManager`
        """
        parameterset = ExperimentParameterSet.objects.filter(
        schema__namespace=self.schema,
        experiment__id=self.experiment_id)

        if not len(parameterset):
            if create:
                experiment = Experiment.objects.get(id=self.experiment_id)
                self.psm = ParameterSetManager(schema=self.schema,
                        parentObject=experiment)
            else:
                return None
        else:
            self.psm = ParameterSetManager(parameterset=parameterset[0])

        return self.psm

    def has_cc_license(self):

        """
        :return: True if there's a cc license parameterset for the experiment
        :rtype: boolean
        """
        parameterset = ExperimentParameterSet.objects.filter(
        schema__namespace=self.schema,
        experiment__id=self.experiment_id)

        self.psm = None
        if not len(parameterset):
            return False
        else:
            return True

    def save_license(self, request):
        """
        Saves a license parameterset with the POST variables from the
        creative commons form
        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        if request.POST['cc_js_want_cc_license'] ==\
            'sure':
            cc_js_result_img = request.POST['cc_js_result_img']
            cc_js_result_name = request.POST['cc_js_result_name']
            cc_js_result_uri = request.POST['cc_js_result_uri']

            self.psm.set_param("license_image", cc_js_result_img,
                "License Image")
            self.psm.set_param("license_name", cc_js_result_name,
                "License Name")
            self.psm.set_param("license_uri", cc_js_result_uri,
                "License URI")
        else:
            self.psm.delete_params('license_image')
            self.psm.delete_params('license_name')
            self.psm.delete_params('license_uri')

            parametersets = ExperimentParameterSet.objects.filter(
            schema__namespace=self.schema,
            experiment__id=self.experiment_id)

            for parameterset in parametersets:
                parameterset.delete()
