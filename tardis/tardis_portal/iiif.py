from lxml import etree
from lxml.etree import Element, SubElement
import json
import mimetypes
from StringIO import StringIO
from urllib2 import urlopen
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, HttpResponseNotFound

from tardis.tardis_portal.models import Dataset_File
from tardis.tardis_portal.auth.decorators import has_datafile_download_access

from wand.exceptions import MissingDelegateError
from wand.image import Image

NSMAP = { None: 'http://library.stanford.edu/iiif/image-api/ns/' }
ALLOWED_MIMETYPES = ['image/jpeg', 'image/png', 'image/tiff',
                     'image/gif', 'image/jp2', 'application/pdf']

def compliance_header(f):
    def wrap(*args, **kwargs):
        response = f(*args, **kwargs)
        if response:
            response['Link'] = r'<http://library.stanford.edu/iiif/image-api/'+\
                               r'compliance.html#level1>;rel="compliesTo"'
        return response
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

def _get_iiif_error(parameter, text):
    error = Element('error', nsmap=NSMAP)
    SubElement(error, 'parameter').text = parameter
    SubElement(error, 'text').text = text
    return etree.tostring(error, method='xml')

def _bad_request(parameter, text):
    return HttpResponse(_get_iiif_error(parameter, text),
                        status=400, mimetype='application/xml')

def _invalid_media_response():
    xml = _get_iiif_error('format',
                          'Image cannot be converted to this format')
    return HttpResponse(xml, status=415, mimetype='application/xml')


def _do_resize(img, size):
    def pct_resize(pct):
        w, h = [int(round(n*pct)) for n in (img.width, img.height)]
        return img.resize(w, h)

    # Width (aspect ratio preserved)
    if size.endswith(','):
        width = float(size[:-1])
        pct_resize(width/img.width)
        return True
    # Height (aspect ratio preserved)
    if size.startswith(','):
        height = float(size[1:])
        pct_resize(height/img.height)
        return True
    # Percent size (aspect ratio preserved)
    if size.startswith('pct:'):
        pct = float(size[4:])/100
        pct_resize(pct)
        return True
    # Width & height specified
    if ',' in size:
        if size.startswith('!'):
            size = size[1:]
            # Maximum dimensions (aspect ratio preserved)
            if img.height < img.width:
                # Width determines resize
                width = float(size.split(',')[0])
                pct_resize(width/img.width)
            else:
                # Height determines resize
                height = float(size.split(',')[1])
                pct_resize(height/img.height)
            return True
        else:
            # Exact dimensions *without* aspect ratio preserved
            w, h = [int(round(float(n))) for n in size.split(',')[:2]]
            img.resize(w, h)
            return True
    return False


@compliance_header
def download_image(request, datafile_id, region, size, rotation, quality, format=None): #@ReservedAssignment
    # Get datafile (and return 404 if absent)
    try:
        datafile = Dataset_File.objects.get(pk=datafile_id)
    except Dataset_File.DoesNotExist:
        return HttpResponseNotFound()
    # Check users has access to datafile
    if not has_datafile_download_access(request=request,
                                        dataset_file_id=datafile.id):
        return HttpResponseNotFound()

    buf = StringIO()
    try:
        with Image(file=urlopen(datafile.get_actual_url())) as img:
            # Handle region
            if region != 'full':
                x, y, w, h = map(lambda x: int(x), region.split(','))
                img.crop(x, y, width=w, height=h)
            # Handle size
            if size != 'full':
                # Check the image isn't empty
                if 0 in (img.height, img.width):
                    return _bad_request('size', 'Cannot resize empty image')
                # Attempt resize
                if not _do_resize(img, size):
                    return _bad_request('size',
                                        'Invalid size argument: %s' % size)
            # Handle rotation
            if rotation:
                img.rotate(float(rotation))
            # Handle quality (mostly by rejecting it)
            if not quality in ['native', 'color']:
                return _get_iiif_error('quality',
                'This server does not support greyscale or bitonal quality.')
            # Handle format
            if format:
                mimetype = mimetypes.types_map['.%s' % format.lower()]
                img.format = format
                if not mimetype in ALLOWED_MIMETYPES:
                    return _invalid_media_response()
            else:
                mimetype = datafile.get_mimetype()
                # If the native format is not allowed, pretend it doesn't exist.
                if not mimetype in ALLOWED_MIMETYPES:
                    return HttpResponseNotFound()
            img.save(file=buf)
            return HttpResponse(buf.getvalue(), mimetype=mimetype)
    except MissingDelegateError:
        if format:
            return _invalid_media_response()
        return HttpResponseNotFound()

@compliance_header
def download_info(request, datafile_id, format): #@ReservedAssignment
    # Get datafile (and return 404 if absent)
    try:
        datafile = Dataset_File.objects.get(pk=datafile_id)
    except Dataset_File.DoesNotExist:
        return HttpResponseNotFound()
    # Check users has access to datafile
    if not has_datafile_download_access(request=request,
                                        dataset_file_id=datafile.id):
        return HttpResponseNotFound()

    with Image(filename=datafile.get_actual_url()) as img:
        data = {'identifier': datafile.id,
                'height': img.height,
                'width':  img.width }

    if format == 'xml':
        info = Element('info', nsmap=NSMAP)
        identifier = SubElement(info, 'identifier')
        identifier.text = datafile_id
        with Image(filename=datafile.get_actual_url()) as img:
            height = SubElement(info, 'height')
            height.text = str(data['height'])
            width = SubElement(info, 'width')
            width.text = str(data['width'])
        return HttpResponse(etree.tostring(info, method='xml'),
                            mimetype="application/xml")
    if format == 'json':
        return HttpResponse(json.dumps(data), mimetype="application/json")
    return HttpResponseNotFound()