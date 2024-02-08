# pylint: disable=http-response-with-json-dumps,http-response-with-content-type-json
import hashlib
import json
import mimetypes
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.cache import patch_cache_control
from django.views.decorators.http import etag

from lxml import etree
from lxml.etree import Element, SubElement
from wand.exceptions import WandException
from wand.image import Image

from .auth.decorators import has_download_access
from .models import DataFile

MAX_AGE = getattr(settings, "DATAFILE_CACHE_MAX_AGE", 60 * 60 * 24 * 7)

NSMAP = {None: "http://library.stanford.edu/iiif/image-api/ns/"}
ALLOWED_MIMETYPES = [
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/gif",
    "image/jp2",
    "application/pdf",
]

mimetypes.add_type("image/jp2", ".jp2")


def compliance_header(f):
    def wrap(*args, **kwargs):
        response = f(*args, **kwargs)
        if response:
            response["Link"] = (
                r"<http://library.stanford.edu/iiif/image-api/"
                + r'compliance.html#level1>;rel="compliesTo"'
            )
        return response

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def _get_iiif_error(parameter, text):
    error = Element("error", nsmap=NSMAP)
    SubElement(error, "parameter").text = parameter
    SubElement(error, "text").text = text
    return etree.tostring(error, method="xml")


def _bad_request(parameter, text):
    return HttpResponse(
        _get_iiif_error(parameter, text), status=400, content_type="application/xml"
    )


def _invalid_media_response():
    xml = _get_iiif_error("format", "Image cannot be converted to this format")
    return HttpResponse(xml, status=415, content_type="application/xml")


def _do_resize(img, size):
    def pct_resize(pct):
        w, h = [int(round(n * pct)) for n in (img.width, img.height)]
        return img.resize(w, h)

    # Width (aspect ratio preserved)
    if size.endswith(","):
        width = float(size[:-1])
        pct_resize(width / img.width)
        return True
    # Height (aspect ratio preserved)
    if size.startswith(","):
        height = float(size[1:])
        pct_resize(height / img.height)
        return True
    # Percent size (aspect ratio preserved)
    if size.startswith("pct:"):
        pct = float(size[4:]) / 100
        pct_resize(pct)
        return True
    # Width & height specified
    if "," in size:
        if size.startswith("!"):
            size = size[1:]
            width, height = map(float, size.split(","))
            image_ratio = float(img.width) / img.height
            # Maximum dimensions (aspect ratio preserved)
            if image_ratio * height > width:
                # Width determines resize
                pct_resize(width / img.width)
            else:
                # Height determines resize
                pct_resize(height / img.height)
            return True
        # Exact dimensions *without* aspect ratio preserved
        w, h = [int(round(float(n))) for n in size.split(",")[:2]]
        img.resize(w, h)
        return True
    return False


def compute_etag(request, datafile_id, *args, **kwargs):
    try:
        datafile = DataFile.objects.get(pk=datafile_id)
    except DataFile.DoesNotExist:
        return None
    if not has_download_access(request=request, obj_id=datafile.id, ct_type="datafile"):
        return None
    # OK, we can compute the Etag without giving anything away now
    # Calculating SHA-512 sums is now optional, so use MD5 sums
    # if SHA-512 sums are unavailable:
    checksum = datafile.sha512sum or datafile.md5sum
    signature = checksum + json.dumps((args, kwargs))
    return hashlib.sha1(signature.encode()).hexdigest()


@etag(compute_etag)
@compliance_header
def download_image(
    request, datafile_id, region, size, rotation, quality, format=None
):  # @ReservedAssignment
    # Get datafile (and return an empty response if absent)
    try:
        datafile = DataFile.objects.get(pk=datafile_id)
    except DataFile.DoesNotExist:
        return HttpResponse("")

    is_public = datafile.is_public_dl()
    if not is_public:
        # Check users has access to datafile
        if not has_download_access(
            request=request, obj_id=datafile.id, ct_type="datafile"
        ):
            return HttpResponse("")

    buf = BytesIO()
    try:
        file_obj = datafile.get_image_data()
        if file_obj is None:
            return HttpResponse("")
        from contextlib import closing

        with closing(file_obj) as f:
            with Image(file=f) as img:
                if len(img.sequence) > 1:
                    img = Image(img.sequence[0])
                # Handle region
                if region != "full":
                    x, y, w, h = map(int, region.split(","))
                    img.crop(x, y, width=w, height=h)
                # Handle size
                if size != "full":
                    # Check the image isn't empty
                    if 0 in (img.height, img.width):
                        return _bad_request("size", "Cannot resize empty image")
                    # Attempt resize
                    if not _do_resize(img, size):
                        return _bad_request("size", "Invalid size argument: %s" % size)
                # Handle rotation
                if rotation:
                    img.rotate(float(rotation))
                # Handle quality (mostly by rejecting it)
                if quality not in ["native", "color"]:
                    return _get_iiif_error(
                        "quality",
                        "This server does not support greyscale or bitonal quality.",
                    )
                # Handle format
                if format:
                    mimetype = mimetypes.types_map[".%s" % format.lower()]
                    img.format = format
                    if mimetype not in ALLOWED_MIMETYPES:
                        return _invalid_media_response()
                else:
                    mimetype = datafile.get_mimetype()
                    # If the native format is not allowed, pretend it doesn't exist.
                    if mimetype not in ALLOWED_MIMETYPES:
                        return HttpResponse("")
                img.save(file=buf)
                response = HttpResponse(buf.getvalue(), content_type=mimetype)
                response["Content-Disposition"] = 'inline; filename="%s.%s"' % (
                    datafile.filename,
                    format,
                )
                # Set Cache
                if is_public:
                    patch_cache_control(response, public=True, max_age=MAX_AGE)
                else:
                    patch_cache_control(response, private=True, max_age=MAX_AGE)
                return response
    except WandException:
        return HttpResponse("")
    except ValueError:
        return HttpResponse("")
    except IOError:
        return HttpResponse("")


@etag(compute_etag)
@compliance_header
def download_info(request, datafile_id, format):  # @ReservedAssignment
    # Get datafile (and return 404 if absent)
    try:
        datafile = DataFile.objects.get(pk=datafile_id)
    except DataFile.DoesNotExist:
        return HttpResponseNotFound()
    # Check users has access to datafile
    if not has_download_access(request=request, obj_id=datafile.id, ct_type="datafile"):
        return HttpResponseNotFound()

    file_obj = datafile.get_file()
    if file_obj is None:
        return HttpResponseNotFound()
    from contextlib import closing

    with closing(file_obj) as f:
        with Image(file=f) as img:
            data = {"identifier": datafile.id, "height": img.height, "width": img.width}

    if format == "xml":
        info = Element("info", nsmap=NSMAP)
        identifier = SubElement(info, "identifier")
        identifier.text = datafile_id
        height = SubElement(info, "height")
        height.text = str(data["height"])
        width = SubElement(info, "width")
        width.text = str(data["width"])
        return HttpResponse(
            etree.tostring(info, method="xml"), content_type="application/xml"
        )
    if format == "json":
        return HttpResponse(json.dumps(data), content_type="application/json")
    return HttpResponseNotFound()
