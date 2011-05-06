'''
RIF CS Profile Module

.. moduleauthor:: Steve Androulakis <steve.androulakis@gmail.com>
'''
from tardis.tardis_portal.publish.interfaces import PublishProvider
from tardis.tardis_portal.models import Experiment, ExperimentParameter, \
    ParameterName, Schema, ExperimentParameterSet
import os
import logging

logger = logging.getLogger(__name__)


class rif_cs_PublishProvider(PublishProvider):

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    name = u'Research Data Australia Profile'

    def execute_publish(self, request):
        """
        Attach the user-selected RIF-CS profile name to the experiment
        as a parameter

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`

        """
        if request.POST['profile']:
            experiment = Experiment.objects.get(id=self.experiment_id)

            profile = request.POST['profile']
            self.save_rif_cs_profile(experiment, profile)

            return {'status': True,
            'message': 'Success'}
        else:
            return {'status': True,
            'message': 'No profiles exist to choose from'}

    def get_context(self, request):
        """
        Display a list of profiles on screen for selection

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`

        """

        rif_cs_profiles = self.get_rif_cs_profile_list()

        selected_profile = "default.xml"

        if self.get_profile():
            selected_profile = self.get_profile()

        return {"rif_cs_profiles": rif_cs_profiles,
                "selected_profile": selected_profile}

    def get_path(self):
        """
        Return the relative template file path to display on screen

        :rtype: string
        """
        return "rif_cs_profile/form.html"

    def get_rif_cs_profile_list(self):
        """
        Return a list of the possible RIF-CS profiles that can
        be applied. Scans the profile directory.

        :rtype: list of strings
        """

        # TODO this is not a scalable or pluggable way of listing
        #  or defining RIF-CS profiles. The current method REQUIRES
        #  branching of the templates directory. instead of using the
        #  built in template resolution tools.
        TARDIS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        profile_dir = os.path.join(TARDIS_ROOT,
                      "profiles/")

        profile_list = list()

        try:
            for f in os.listdir(profile_dir):
                if not os.path.isfile(profile_dir + f) or \
                       f.startswith('.') or not f.endswith('.xml'):
                    continue
                profile_list.append(f)
        except OSError:
            logger.error("Can't find profile directory " +
            "or no profiles available")

        return profile_list

    def save_rif_cs_profile(self, experiment, profile):
        """
        Save selected profile choice as experiment parameter
        """
        namespace = "http://monash.edu.au/rif-cs/profile/"
        schema = None
        try:
            schema = Schema.objects.get(
                namespace__exact=namespace)
        except Schema.DoesNotExist:
            logger.debug('Schema ' + namespace +
            ' does not exist. Creating.')
            schema = Schema(namespace=namespace)
            schema.save()

        parametername = ParameterName.objects.get(
            schema__namespace__exact=schema.namespace,
            name="profile")

        parameterset = None
        try:
            parameterset = \
                         ExperimentParameterSet.objects.get(\
                                schema=schema,
                                experiment=experiment)

        except ExperimentParameterSet.DoesNotExist, e:
            parameterset = ExperimentParameterSet(\
                                schema=schema,
                                experiment=experiment)

            parameterset.save()

        # if a profile param already exists
        if self.get_profile():
            ep = ExperimentParameter.objects.filter(name=parametername,
            parameterset=parameterset,
            parameterset__experiment__id=self.experiment_id)

            for p in ep:
                p.delete()

        ep = ExperimentParameter(
            parameterset=parameterset,
            name=parametername,
            string_value=profile,
            numerical_value=None)
        ep.save()

    def get_profile(self):
        """
        Retrieve existing rif-cs profile for experiment, if any
        """

        ep = ExperimentParameter.objects.filter(name__name='profile',
        parameterset__schema__namespace='http://monash.edu.au/rif-cs/profile/',
        parameterset__experiment__id=self.experiment_id)

        if len(ep):
            return ep[0].string_value
        else:
            return None
