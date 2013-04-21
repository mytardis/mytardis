'''
Filepicker.io button view and upload handler
'''
import json
import logging

from django.http import HttpResponse
from django.template import Context

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import Dataset_File
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.staging import write_uploaded_file_to_dataset

import tardis.apps.filepicker.filepicker_settings as filepicker_settings

logger = logging.getLogger(__name__)


@authz.upload_auth
@authz.dataset_write_permissions_required
def upload_button(request, dataset_id):
    '''
    renders the filepicker button/widget via an ajax call
    '''
    filepicker_api_key = filepicker_settings.filepicker_api_key

    c = Context({'filepicker_api_key': filepicker_api_key,
                 'dataset_id': dataset_id, })

    return HttpResponse(render_response_index(
        request, 'filepicker/filepicker.html', c))


@authz.upload_auth
@authz.dataset_write_permissions_required
def fpupload(request, dataset_id):
    """
    Uploads all files picked by filepicker to the dataset

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param dataset_id: the dataset_id
    :type dataset_id: integer
    :returns: boolean true if successful
    :rtype: bool
    """

    dataset = Dataset.objects.get(id=dataset_id)
    logger.debug('called fpupload')

    if request.method == 'POST':
        logger.debug('got POST')
        from django_filepicker.utils import FilepickerFile
        for key, val in request.POST.items():
            splits = val.split(",")
            for url in splits:
                try:
                    fp = FilepickerFile(url)
                except ValueError:
                    pass
                else:
                    picked_file = fp.get_file()
                    filepath = write_uploaded_file_to_dataset(dataset,
                                                              picked_file)
                    datafile = Dataset_File(dataset=dataset,
                                            filename=picked_file.name,
                                            url=filepath,
                                            size=picked_file.size,
                                            protocol='')
                    datafile.verify(allowEmptyChecksums=True)
                    datafile.save()

    return HttpResponse(json.dumps({"result": True}))
