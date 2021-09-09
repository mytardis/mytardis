"""
helper functions used by other views
"""

import json
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat

from ..models.datafile import DataFile

logger = logging.getLogger(__name__)


def _redirect_303(*args, **kwargs):
    response = redirect(*args, **kwargs)
    response.status_code = 303
    return response


def _add_protocols_and_organizations(request, collection_object, c):
    """Add the protocol, format and organization details for
    archive requests.  Since the MacOSX archiver can't cope with
    streaming ZIP, the best way to avoid 'user disappointment'
    is to not offer ZIP."""

    if getattr(settings, 'USER_AGENT_SENSING', False) and \
            request.user_agent:
        logger.debug('user_agent.os.family: %s' % request.user_agent.os.family)
        cannot_do_zip = request.user_agent.os.family in ['Macintosh',
                                                         'Mac OS X']
    else:
        cannot_do_zip = False

    if collection_object:
        c['protocol'] = []
        download_urls = collection_object.get_download_urls()
        for key, value in download_urls.items():
            if cannot_do_zip and key == 'zip':
                continue
            c['protocol'] += [[key, value]]

    formats = getattr(settings, 'DEFAULT_ARCHIVE_FORMATS', ['tgz', 'tar'])
    c['default_format'] = list(filter(
        lambda x: not (cannot_do_zip and x == 'zip'), formats))[0]

    from ..download import get_download_organizations
    c['organization'] = get_download_organizations()
    c['default_organization'] = getattr(
        settings, 'DEFAULT_PATH_MAPPER', 'classic')


def get_dataset_info(dataset, request, include_thumbnail=False, exclude=None):  # too complex # noqa
    obj = model_to_dict(dataset)

    # Changed in Django 1.10: Private API django.forms.models.model_to_dict()
    # returns a queryset rather than a list of primary keys for ManyToManyFields
    obj['experiments'] = [exp.id for exp in obj['experiments']]

    if exclude is None or 'datafiles' not in exclude or 'file_count' \
        not in exclude:
        if settings.ONLY_EXPERIMENT_ACLS:
            datafiles = list(DataFile.objects.select_related("dataset").filter(
                           dataset__id=dataset.id).values_list('id', flat=True))
        else:
            datafiles = list(DataFile.safe.all(request.user).filter(
                           dataset__id=dataset.id).values_list('id', flat=True))
        if exclude is None or 'datafiles' not in exclude:
            obj['datafiles'] = datafiles
        if exclude is None or 'file_count' not in exclude:
            obj['file_count'] = len(datafiles)

    obj['url'] = dataset.get_absolute_url()

    if exclude is None or 'size' not in exclude:
        obj['size'] = dataset.get_size(request.user)
        obj['size_human_readable'] = filesizeformat(obj['size'])

    if (dataset.instrument
        and (exclude is None or 'instrument' not in exclude)):
        obj['instrument'] = dataset.instrument.name
        obj['show_instr_facil'] = True
        if (dataset.instrument.facility
            and (exclude is None or 'facility' not in exclude)):
            obj['facility'] = dataset.instrument.facility.name

    # Whether dataset thumbnails are enabled, i.e.
    # include a thumbnail <div> in every tile:
    obj['show_dataset_thumbnails'] = getattr(
        settings, "SHOW_DATASET_THUMBNAILS", True)

    # Whether this dataset tile's thumbnail is enabled.
    # If not, still include a blank thumbnail <div>:
    if include_thumbnail and dataset.image:
        try:
            obj['thumbnail'] = reverse(
                'tardis.tardis_portal.views.dataset_thumbnail',
                kwargs={'dataset_id': dataset.id})
        except AttributeError:
            pass

    if exclude is None or 'datasettype' not in exclude:
        if hasattr(settings, "DATASET_VIEWS"):
            schemas = {}
            for ps in dataset.getParameterSets():
                schemas[ps.schema.namespace] = ps.schema
            for ns, _ in settings.DATASET_VIEWS:
                if ns in schemas:
                    obj["datasettype"] = schemas[ns].name
                    break
    return obj


def remove_csrf_token(request):
    '''
    rather than fixing the form code that loops over all POST entries
    indiscriminately, I am removing the csrf token with this hack.
    This is only required in certain form code and can be removed should
    this ever be fixed
    '''
    new_post_dict = request.POST.copy()
    del(new_post_dict['csrfmiddlewaretoken'])
    request.POST = new_post_dict
    return request


class HttpResponseMethodNotAllowed(HttpResponse):
    status_code = 303

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self["Allow"] = kwargs['allow']
        except:
            self["Allow"] = 'GET'


class HttpResponseSeeAlso(HttpResponseRedirect):
    status_code = 303


def feedback(request):
    if request.method == 'POST':
        feedback_data = json.loads(request.POST['data'].decode())
        message = feedback_data[0]['Issue']
        img_base64 = feedback_data[1]
        img = img_base64.replace('data:image/png;base64,', '').decode('base64')
        admin_emails = [v for k, v in settings.ADMINS]
        email = EmailMessage('[TARDIS] User feedback', message,
                             'store.star.help@monash.edu', admin_emails)
        email.attach('screenshot.png', img, 'image/png')
        email.send()
        return HttpResponse('OK')
    return redirect('/')
