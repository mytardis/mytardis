"""
views that return data useful only to other machines (but not JSON)
"""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied

from ..auth import auth_service
from ..auth import decorators as authz
from ..auth.localdb_auth import auth_key as localdb_auth_key
from ..models import Experiment
from ..shortcuts import (
    render_response_index,
    return_response_error,
    return_response_not_found,
)

logger = logging.getLogger(__name__)


@authz.experiment_access_required
def view_rifcs(request, experiment_id):
    """View the rif-cs of an existing experiment.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be viewed
    :type experiment_id: string
    :returns: a HttpResponse
    :rtype: :class:`django.http.HttpResponse`

    """
    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    try:
        rifcs_provs = settings.RIFCS_PROVIDERS
    except AttributeError:
        rifcs_provs = ()

    from ..publish.publishservice import PublishService
    pservice = PublishService(rifcs_provs, experiment)
    context = pservice.get_context()
    if context is None:
        # return error page or something
        return return_response_error(request)

    template = pservice.get_template()
    return render_response_index(
        request, template, context, content_type="text/xml")


def site_settings(request):

    if request.method == 'POST':
        if 'username' in request.POST and 'password' in request.POST:

            user = auth_service.authenticate(request=request,
                                             authMethod=localdb_auth_key)
            if user is not None:
                if user.is_staff:

                    with open(settings.GRID_PROXY_FILE, 'r') as x509:
                        c = {
                            'baseurl': request.build_absolute_uri('/'),
                            'proxy': x509.read(), 'filestorepath':
                            settings.FILE_STORE_PATH}
                    return render_response_index(
                        request,
                        'tardis_portal/site_settings.xml',
                        c, content_type='application/xml')

    return return_response_error(request)
