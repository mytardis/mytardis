'''
Publish Service (for working with PublishProvider instances)

.. moduleauthor:: Steve Androulakis <steve.androulakis@monash.edu>
'''
from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from tardis.tardis_portal.models import Experiment
import logging

logger = logging.getLogger(__name__)

class PublishService():

    def __init__(self, experiment_id, settings=settings):
        self._publish_providers = []
        self._initialised = False
        self.settings = settings
        self.experiment_id = experiment_id

    def _manual_init(self):
        """Manual init had to be called by all the functions of the PublishService
        class to initialise the instance variables. This block of code used to
        be in the __init__ function but has been moved to its own init function
        to get around the problems with cyclic imports to static variables
        being exported from auth related modules.

        """
        for pp in self.settings.PUBLISH_PROVIDERS:
            self._publish_providers.append(self._safe_import(pp))
        self._initialised = True

    def _safe_import(self, path):
        try:
            dot = path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured(\
                '%s isn\'t a middleware module' % path)
        publish_module, publish_classname = path[:dot], path[dot + 1:]
        try:
            mod = import_module(publish_module)
        except ImportError, e:
            raise ImproperlyConfigured(\
                'Error importing publish module %s: "%s"' %
                                       (publish_module, e))
        try:
            publish_class = getattr(mod, publish_classname)
        except AttributeError:
            raise ImproperlyConfigured(\
                'Publish module "%s" does not define a "%s" class' %
                                       (publish_module, publish_classname))

        publish_instance = publish_class(self.experiment_id)
        return publish_instance

    def get_publishers(self):
        """Return a list publish providers

        """
        if not self._initialised:
            self._manual_init()

        publicaton_list = [pp for pp in self._publish_providers]
        return publicaton_list

    def get_template_paths(self):
        """Returns a list of relative file paths to html templates

        """
        if not self._initialised:
            self._manual_init()
        path_list = []
        for pp in self._publish_providers:
            # logger.debug("group provider: " + gp.name)
            path_list.append(pp.get_path())
        return path_list

    def get_contexts(self, request):
        """Gets context dictionaries for each PublishProvider

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        if not self._initialised:
            self._manual_init()
        contexts = {}
        for pp in self._publish_providers:
            # logger.debug("group provider: " + gp.name)
            context = pp.get_context(request)
            if context:
                contexts = dict(contexts, **context)
        return contexts

    def execute_publishers(self, request):
        """Executes each publish provider in a chain.
        If any publish provider fails then the experiment is not made public

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        if not self._initialised:
            self._manual_init()

        pp_status_list = []
        for pp in self._publish_providers:

            pp_status = False
            pp_result = "Successful"

            try:
                pp_response = pp.execute_publish(request)
            except Exception as inst:
                # perhaps erroneous logic to be fixed later..
                exp = Experiment.objects.get(id=self.experiment_id)
                exp.public = False
                exp.save()

                logger.error('Publish Provider Exception: ' +
                pp.name + ' on exp: ' + str(self.experiment_id) +
                ' failed with message "' +
                str(inst) + '""')

                pp_response = {'status': False, 'message': str(inst)}

            if pp_response['status']:
                logger.info('Publish Provider: ' +
                pp.name + ' executed on Exp: ' +
                str(self.experiment_id) + ' with success: ' +
                str(pp_response['status']) + ' and message: ' +
                pp_response['message'])
            else:
                logger.error('Publish Provider: ' +
                pp.name + ' executed on Exp: ' +
                str(self.experiment_id) + ' FAILED with message: ' +
                pp_response['message'])

            pp_status_list.append({'name': pp.name,
            'status': pp_response['status'],
            'message': pp_response['message']})
        return pp_status_list
