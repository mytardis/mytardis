# -*- coding: utf-8 -*-

import io
import json
from os import path
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms.forms import NON_FIELD_ERRORS
from django.http import HttpResponse, HttpResponseServerError, StreamingHttpResponse
from django.shortcuts import render

from paramiko import RSAKey
from paramiko.ssh_exception import SSHException
from PIL import Image, ImageDraw, ImageFont

from tardis.tardis_portal.auth.decorators import has_download_access

from .forms import KeyGenerateForm
from .models import SFTPPublicKey


@login_required
def sftp_access(request):
    """
    Show dynamically generated instructions on how to connect to SFTP
    :param Request request: HttpRequest
    :return: HttpResponse
    :rtype: HttpResponse
    """
    from tardis.tardis_portal.download import make_mapper

    object_type = request.GET.get("object_type")
    object_id = request.GET.get("object_id")
    sftp_start_dir = ""
    if object_type and object_id:
        ct = ContentType.objects.get_by_natural_key("tardis_portal", object_type)
        item = ct.model_class().objects.get(id=object_id)
        if object_type == "experiment":
            exps = [item]
            dataset = None
            datafile = None
        else:
            if object_type == "dataset":
                dataset = item
                datafile = None
            elif object_type == "datafile":
                datafile = item
                dataset = datafile.dataset
            exps = dataset.experiments.all()
        allowed_exps = []
        for exp in exps:
            if has_download_access(request, exp.id, "experiment"):
                allowed_exps.append(exp)
        if allowed_exps:
            path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)
            exp = allowed_exps[0]
            path_parts = [
                "/home",
                request.user.username,
                "experiments",
                path_mapper(exp),
            ]
            if dataset is not None:
                path_parts.append(path_mapper(dataset))
            if datafile is not None:
                path_parts.append(datafile.directory)
            sftp_start_dir = path.join(*path_parts)

    if request.user.userprofile.isDjangoAccount:
        sftp_username = request.user.username
    else:
        login_attr = getattr(settings, "SFTP_USERNAME_ATTRIBUTE", "email")
        sftp_username = getattr(request.user, login_attr)
    c = {
        "sftp_host": request.get_host().split(":")[0],
        "sftp_port": getattr(settings, "SFTP_PORT", 2200),
        "sftp_username": sftp_username,
        "sftp_start_dir": sftp_start_dir,
        "site_name": getattr(settings, "SITE_TITLE", "MyTardis"),
    }
    c["sftp_url"] = "sftp://{}@{}:{}{}".format(
        c["sftp_username"], c["sftp_host"], c["sftp_port"], c["sftp_start_dir"]
    )
    return render(request, template_name="sftp/index.html", context=c)


@login_required
def cybderduck_connection_window(request):
    base_image = "tardis/apps/sftp/images/cyberduck_connection_blank.png"
    font_file = "tardis/apps/sftp/fonts/roboto.ttf"
    base = Image.open(base_image)
    font = ImageFont.truetype(font_file, 22)
    draw = ImageDraw.Draw(base)

    if request.user.userprofile.isDjangoAccount:
        sftp_username = request.user.username
    else:
        login_attr = getattr(settings, "SFTP_USERNAME_ATTRIBUTE", "email")
        sftp_username = getattr(request.user, login_attr)

    sftp_host = request.get_host().split(":")[0]
    sftp_port = str(getattr(settings, "SFTP_PORT", 2200))
    info = [
        {"location": (532, 322), "text": sftp_host},
        {"location": (1096, 322), "text": sftp_port},
        {"location": (532, 420), "text": sftp_username},
    ]
    url = {
        "location": (532, 370),
        "text": "sftp://{}@{}:{}/".format(sftp_username, sftp_host, sftp_port),
    }
    for text in info:
        draw.text(text["location"], text["text"], font=font, fill=(0, 0, 0))

    def draw_underlined_text(draw, pos, text, font, **options):
        l, t, r, b = draw.textbbox((pos[0], pos[1]), text=text, font=font)
        twidth = r - l
        theight = t - b
        lx, ly = pos[0], pos[1] + theight - 2
        draw.text(pos, text, font=font, **options)
        draw.line((lx, ly, lx + twidth - 2, ly), **options)

    url_font = ImageFont.truetype(font_file, 18)
    url_colour = (0, 49, 249)
    draw_underlined_text(draw, url["location"], url["text"], url_font, fill=url_colour)
    response = HttpResponse(content_type="image/png")
    base.save(response, "PNG")
    base.save("foo.png")
    return response


@login_required
def sftp_keys(request):
    """Generate an RSA key pair for a user.

    Generates a key pair, stores the public part of the key and provides a one
    time opportunity for the user to download the private part of the key.

    :param request: http request
    :type request: HttpRequest
    :return: either returns form on GET request or private key download on POST
        request
    :rtype: HttpResponse
    """
    if request.method == "POST":
        form = KeyGenerateForm(request.POST)
        if form.is_valid():
            user = request.user
            key_name = form.cleaned_data["name"]
            key = RSAKey.generate(4096)
            key_file = io.StringIO()
            try:
                key.write_private_key(key_file)
            except (IOError, SSHException):
                return HttpResponseServerError(
                    json.dumps(
                        {
                            "error": "Oops! Failed to generate key. "
                            "Please try again later."
                        }
                    ),
                    content_type="application/json",
                )
            # Create SFTPPublicKey record
            SFTPPublicKey.objects.create(
                user=user,
                name=key_name,
                key_type=key.get_name(),
                public_key=key.get_base64(),
            )

            # Move to beginning of file and stream HTTPReponse
            key_file.seek(0)
            response = StreamingHttpResponse(
                FileWrapper(key_file), content_type="application/octet-stream"
            )
            response["Content-Disposition"] = f"attachment; filename='{key_name}'"

            return response
    else:
        form = KeyGenerateForm()

        enable_generate = False
        if getattr(settings, "REQUIRE_SSL_TO_GENERATE_KEY", True):
            enable_generate = request.is_secure()
        else:
            enable_generate = True

        if not enable_generate:
            form.fields["name"].disabled = True
            form.errors[NON_FIELD_ERRORS] = form.error_class(
                [
                    "The SSH key generation feature has been disabled because your "
                    "connection is insecure. Please contact your %s service administrator "
                    "about securing your connection."
                    % getattr(settings, "SITE_TITLE", "MyTardis")
                ]
            )

    return render(
        request, "sftp/keys.html", {"form": form, "enable_generate": enable_generate}
    )
