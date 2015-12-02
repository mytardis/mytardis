"""
views that return images or route to images
"""

from base64 import b64decode
import logging
from os import path

from PIL import Image, ImageFont, ImageDraw
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.cache import never_cache

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import ExperimentParameter, DatasetParameter, \
    DatafileParameter, Dataset
from tardis.tardis_portal.shortcuts import return_response_error

logger = logging.getLogger(__name__)


@login_required
def cybderduck_connection_window(request):
    base_image = ("tardis/tardis_portal/templates/images/"
                  "cyberduck_connection_blank.png")
    font_file = "tardis/tardis_portal/templates/fonts/roboto.ttf"
    base = Image.open(base_image)
    font = ImageFont.truetype(font_file, 13)
    draw = ImageDraw.Draw(base)
    if request.user.userprofile.isDjangoAccount:
        sftp_username = request.user.username
    else:
        sftp_username = request.user.email
    sftp_host = request.get_host().split(':')[0]
    sftp_port = str(getattr(settings, 'SFTP_PORT', 2200))
    info = [
        {'location': (247, 170),
         'text': sftp_host},
        {'location': (530, 169),
         'text': sftp_port},
        {'location': (247, 217),
         'text': sftp_username},
    ]
    url = {'location': (241, 195),
           'text': 'sftp://{}@{}:{}/'.format(
               sftp_username,
               sftp_host,
               sftp_port)}
    for text in info:
        draw.text(text['location'], text['text'], font=font,
                  fill=(0, 0, 0))

    def draw_underlined_text(draw, pos, text, font, **options):
        twidth, theight = draw.textsize(text, font=font)
        lx, ly = pos[0], pos[1] + theight - 2
        draw.text(pos, text, font=font, **options)
        draw.line((lx, ly, lx + twidth - 2, ly), **options)

    url_font = ImageFont.truetype(font_file, 11)
    url_colour = (0, 49, 249)
    draw_underlined_text(draw, url['location'],
                         url['text'], url_font, fill=url_colour)
    response = HttpResponse(content_type='image/png')
    base.save(response, "PNG")
    base.save("foo.png")
    return response


@never_cache
def load_image(request, parameter):
    file_path = path.abspath(path.join(settings.METADATA_STORE_PATH,
                                       parameter.string_value))

    from django.core.servers.basehttp import FileWrapper
    try:
        wrapper = FileWrapper(file(file_path))
    except IOError:
        return HttpResponseNotFound()
    return HttpResponse(wrapper, content_type=parameter.name.units)


def load_experiment_image(request, parameter_id):
    parameter = ExperimentParameter.objects.get(pk=parameter_id)
    experiment_id = parameter.parameterset.experiment.id
    if authz.has_experiment_access(request, experiment_id):
        return load_image(request, parameter)
    else:
        return return_response_error(request)


def load_dataset_image(request, parameter_id):
    parameter = DatasetParameter.objects.get(pk=parameter_id)
    dataset = parameter.parameterset.dataset
    if authz.has_dataset_access(request, dataset.id):
        return load_image(request, parameter)
    else:
        return return_response_error(request)


def load_datafile_image(request, parameter_id):
    try:
        parameter = DatafileParameter.objects.get(pk=parameter_id)
    except DatafileParameter.DoesNotExist:
        return HttpResponseNotFound()
    datafile = parameter.parameterset.datafile
    if authz.has_datafile_access(request, datafile.id):
        return load_image(request, parameter)
    else:
        return return_response_error(request)


@authz.experiment_access_required
def display_experiment_image(
        request, experiment_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_experiment_access(request, experiment_id):
        return return_response_error(request)

    image = ExperimentParameter.objects.get(name__name=parameter_name,
                                            parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), content_type='image/jpeg')


@authz.dataset_access_required
def display_dataset_image(
        request, dataset_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_dataset_access(request, dataset_id):
        return return_response_error(request)

    image = DatasetParameter.objects.get(name__name=parameter_name,
                                         parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), content_type='image/jpeg')


@authz.datafile_access_required
def display_datafile_image(
        request, datafile_id, parameterset_id, parameter_name):

    # TODO handle not exist

    if not authz.has_datafile_access(request, datafile_id):
        return return_response_error(request)

    image = DatafileParameter.objects.get(name__name=parameter_name,
                                          parameterset=parameterset_id)

    return HttpResponse(b64decode(image.string_value), content_type='image/jpeg')



@authz.dataset_access_required
def dataset_thumbnail(request, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    tn_url = dataset.get_thumbnail_url()
    if tn_url is None:
        return HttpResponseNotFound()
    return HttpResponseRedirect(tn_url)
