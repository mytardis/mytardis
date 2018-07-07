# -*- coding: utf-8 -*-

import base64
from os import path

from binascii import hexlify
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.shortcuts import render
from paramiko.rsakey import RSAKey
from paramiko.py3compat import u
from PIL import Image, ImageFont, ImageDraw

from tardis.tardis_portal.auth.decorators import has_experiment_download_access
from tardis.sftp.models import SFTPPublicKey


@login_required
def sftp_access(request):
    """
    Show dynamically generated instructions on how to connect to SFTP
    :param Request request: HttpRequest
    :return: HttpResponse
    :rtype: HttpResponse
    """
    from tardis.tardis_portal.download import make_mapper
    object_type = request.GET.get('object_type')
    object_id = request.GET.get('object_id')
    sftp_start_dir = ''
    if object_type and object_id:
        ct = ContentType.objects.get_by_natural_key(
            'tardis_portal', object_type)
        item = ct.model_class().objects.get(id=object_id)
        if object_type == 'experiment':
            exps = [item]
            dataset = None
            datafile = None
        else:
            if object_type == 'dataset':
                dataset = item
                datafile = None
            elif object_type == 'datafile':
                datafile = item
                dataset = datafile.dataset
            exps = dataset.experiments.all()
        allowed_exps = []
        for exp in exps:
            if has_experiment_download_access(request, exp.id):
                allowed_exps.append(exp)
        if allowed_exps:
            path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER,
                                      rootdir=None)
            exp = allowed_exps[0]
            path_parts = ['/home', request.user.username, 'experiments',
                          path_mapper(exp)]
            if dataset is not None:
                path_parts.append(path_mapper(dataset))
            if datafile is not None:
                path_parts.append(datafile.directory)
            sftp_start_dir = path.join(*path_parts)

    if request.user.userprofile.isDjangoAccount:
        sftp_username = request.user.username
    else:
        login_attr = getattr(settings, 'SFTP_USERNAME_ATTRIBUTE', 'email')
        sftp_username = getattr(request.user, login_attr)
    c = {
        'sftp_host': request.get_host().split(':')[0],
        'sftp_port': getattr(settings, 'SFTP_PORT', 2200),
        'sftp_username': sftp_username,
        'sftp_start_dir': sftp_start_dir,
        'site_name': getattr(settings, 'SITE_TITLE', 'MyTardis'),
    }
    c['sftp_url'] = 'sftp://{}@{}:{}{}'.format(
        c['sftp_username'],
        c['sftp_host'],
        c['sftp_port'],
        c['sftp_start_dir'])
    return render(request, template_name='sftp/index.html', context=c)


@login_required
def manage_keys(request):
    user =  request.user
    keys = SFTPPublicKey.objects.filter(user=user)

    def _get_key_data(key):
        k = RSAKey(data=base64.b64decode(key.public_key))
        return {
            'id': key.id,
            'name': key.name,
            'fingerprint': u(hexlify(k.get_fingerprint())),
            'added': str(key.added)
        }

    c = {
        'keys': map(_get_key_data, keys) if keys.count() > 0 else []
    }
    return render(request, template_name='sftp/keys.html', context=c)

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
        login_attr = getattr(settings, 'SFTP_USERNAME_ATTRIBUTE', 'email')
        sftp_username = getattr(request.user, login_attr)

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
