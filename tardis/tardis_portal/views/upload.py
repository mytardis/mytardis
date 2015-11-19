"""
views for uploading files via HTTP
"""

import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import Dataset, DataFile

logger = logging.getLogger(__name__)


def upload_complete(request,
                    template_name='tardis_portal/upload_complete.html'):
    """
    The ajax-loaded result of a file being uploaded

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :type template_name: string
    :rtype: :class:`django.http.HttpResponse`
    """

    c = {
        'numberOfFiles': request.POST['filesUploaded'],
        'bytes': request.POST['allBytesLoaded'],
        'speed': request.POST['speed'],
        'errorCount': request.POST['errorCount'],
        }
    return render_to_response(template_name, c)


@authz.upload_auth
@authz.dataset_write_permissions_required
def upload(request, dataset_id):
    """
    Uploads a datafile to the store and datafile metadata

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :returns: boolean true if successful
    :rtype: bool
    """

    dataset = Dataset.objects.get(id=dataset_id)

    logger.debug('called upload')
    if request.method == 'POST':
        logger.debug('got POST')
        if request.FILES:

            uploaded_file_post = request.FILES['Filedata']
            logger.debug('done upload')
            datafile = DataFile(dataset=dataset,
                                filename=uploaded_file_post.name,
                                size=uploaded_file_post.size)
            datafile.save(require_checksums=False)
            logger.debug('created file')
            datafile.file_object = uploaded_file_post
            logger.debug('saved datafile')

    return HttpResponse('True')


@authz.dataset_write_permissions_required
def upload_files(request, dataset_id,
                 template_name='tardis_portal/ajax/upload_files.html'):
    """
    Creates an Uploadify 'create files' button with a dataset
    destination. `A workaround for a JQuery Dialog conflict\
    <http://www.uploadify.com/forums/discussion/3348/
        uploadify-in-jquery-ui-dialog-modal-causes-double-queue-item/p1>`_

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :returns: A view containing an Uploadify *create files* button
    """
    if 'message' in request.GET:
        message = request.GET['message']
    else:
        message = "Upload Files to Dataset"
    url = reverse('tardis.tardis_portal.views.upload_complete')
    c = {'upload_complete_url': url,
         'dataset_id': dataset_id,
         'message': message,
         'session_id': request.session.session_key
    }
    return render_to_response(template_name, c)
