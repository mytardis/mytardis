"""
views for uploading files via HTTP
"""

import logging

from django.http import HttpResponse
from django.shortcuts import render

from ..auth import decorators as authz
from ..models import Dataset, DataFile, DatafileACL

logger = logging.getLogger(__name__)


def upload_complete(request,
                    template_name='tardis_portal/upload_complete.html'):
    """
    The ajax-loaded result of a file being uploaded

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param template_name: the path of the template to render
    :type template_name: string
    :returns: an HttpResponse
    :rtype: :class:`django.http.HttpResponse`
    """

    c = {
        'numberOfFiles': request.POST['filesUploaded'],
        'bytes': request.POST['allBytesLoaded'],
        'speed': request.POST['speed'],
        'errorCount': request.POST['errorCount'],
        }
    return render(request, template_name, c)


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

            if not settings.ONLY_EXPERIMENT_ACLS:
                # add default ACL
                acl = DatafileACL(datafile=datafile,
                                  user=request.user,
                                  canRead=True,
                                  canWrite=True,
                                  canDelete=True,
                                  isOwner=True,
                                  aclOwnershipType=DatafileACL.OWNER_OWNED)
                acl.save()

    return HttpResponse('True')
