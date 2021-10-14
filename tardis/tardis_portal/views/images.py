"""
views that return images or route to images
"""

from base64 import b64decode
import logging
from os import path

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.cache import never_cache

from ..auth import decorators as authz
from ..models import ExperimentParameter, DatasetParameter, \
    DatafileParameter, Dataset
from ..shortcuts import return_response_error

logger = logging.getLogger(__name__)


@never_cache
def load_image(request, parameter):
    file_path = path.abspath(path.join(settings.METADATA_STORE_PATH,
                                       parameter.string_value))

    from wsgiref.util import FileWrapper
    try:
        wrapper = FileWrapper(open(file_path, 'rb'))
    except IOError:
        return HttpResponseNotFound()
    return HttpResponse(wrapper, content_type=parameter.name.units)


def load_experiment_image(request, parameter_id):
    parameter = ExperimentParameter.objects.get(pk=parameter_id)
    experiment_id = parameter.parameterset.experiment.id
    if authz.has_download_access(request, experiment_id, "experiment"):
        return load_image(request, parameter)
    return return_response_error(request)


def load_dataset_image(request, parameter_id):
    parameter = DatasetParameter.objects.get(pk=parameter_id)
    dataset = parameter.parameterset.dataset
    if authz.has_download_access(request, dataset.id, "dataset"):
        return load_image(request, parameter)
    return return_response_error(request)


def load_datafile_image(request, parameter_id):
    try:
        parameter = DatafileParameter.objects.get(pk=parameter_id)
    except DatafileParameter.DoesNotExist:
        return HttpResponseNotFound()
    datafile = parameter.parameterset.datafile
    if authz.has_download_access(request, datafile.id, "datafile"):
        return load_image(request, parameter)
    return return_response_error(request)


@authz.experiment_download_required
def display_experiment_image(
        request, experiment_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_download_access(request, experiment_id, "experiment"):
        return return_response_error(request)

    image = ExperimentParameter.objects.get(name__name=parameter_name,
                                            parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), content_type='image/jpeg')


@authz.dataset_download_required
def display_dataset_image(
        request, dataset_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_download_access(request, dataset_id, "dataset"):
        return return_response_error(request)

    image = DatasetParameter.objects.get(name__name=parameter_name,
                                         parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), content_type='image/jpeg')


@authz.datafile_download_required
def display_datafile_image(
        request, datafile_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_download_access(request, datafile_id, "datafile"):
        return return_response_error(request)

    image = DatafileParameter.objects.get(name__name=parameter_name,
                                          parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), content_type='image/jpeg')



@authz.dataset_download_required
def dataset_thumbnail(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    tn_url = dataset.get_thumbnail_url()
    if tn_url is None:
        return HttpResponseNotFound()
    return HttpResponseRedirect(tn_url)
