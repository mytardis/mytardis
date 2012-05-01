# -*- coding: utf-8 -*-

"""
download.py

.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>

"""
import logging
import subprocess
import urllib
from urllib2 import urlopen
from os import path, devnull

from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotFound
from django.conf import settings

from tardis.tardis_portal.models import *
from tardis.tardis_portal.auth.decorators import *
from tardis.tardis_portal.views import return_response_not_found, \
    return_response_error

try:
    from wand.image import Image
    IMAGEMAGICK_AVAILABLE = True
except (AttributeError, ImportError):
    IMAGEMAGICK_AVAILABLE = False

logger = logging.getLogger(__name__)

MIMETYPES_TO_VIEW_AS_PNG = ['image/tiff']

def view_datafile(request, datafile_id):
    # Get datafile (and return 404 if absent)
    try:
        datafile = Dataset_File.objects.get(pk=datafile_id)
    except Dataset_File.DoesNotExist:
        return return_response_not_found(request)
    # Check users has access to datafile
    if not has_datafile_access(request=request, dataset_file_id=datafile.id):
        return return_response_error(request)
    # Get actual url for datafile
    file_url = _get_actual_url(datafile)
    mimetype = datafile.get_mimetype()
    if IMAGEMAGICK_AVAILABLE and mimetype in MIMETYPES_TO_VIEW_AS_PNG:
        with Image(file=urlopen(file_url)) as img:
            img.format = 'png'
            content = img.make_blob()
        # Should show up as a PNG file
        response = HttpResponse(content, mimetype='image/png')
        response['Content-Disposition'] = \
            'inline; filename="%s.png"' % datafile.filename
    else:
        response = _create_download_response(datafile, file_url,
                                             disposition='inline')
    return response

def download_datafile(request, datafile_id):
    # Get datafile (and return 404 if absent)
    try:
        datafile = Dataset_File.objects.get(pk=datafile_id)
    except Dataset_File.DoesNotExist:
        return return_response_not_found(request)
    # Check users has access to datafile
    if not has_datafile_access(request=request, dataset_file_id=datafile.id):
        return return_response_error(request)
    # Get actual url for datafile
    file_url = _get_actual_url(datafile)
    if not file_url:
        # If file path doesn't resolve, return not found
        return return_response_not_found(request)
    # Just redirect for remote files
    if not file_url.startswith('file://'):
        return HttpResponseRedirect(datafile.url)
    # Send local file
    try:
        return _create_download_response(datafile, file_url)
    except IOError:
        # If we can't read the file, return not found
        return return_response_not_found(request)

def _get_actual_url(datafile):
    # Remote files are easy
    if any(map(datafile.url.startswith, ['http://', 'https://', 'ftp://'])):
        return datafile.url
    # Otherwise, resolve actual file system path
    file_path = datafile.get_absolute_filepath()
    if path.isfile(file_path):
        return 'file://'+file_path
    return None

def _create_download_response(datafile, file_url, disposition='attachment'):
    wrapper = FileWrapper(urlopen(file_url))
    response = HttpResponse(wrapper,
                            mimetype=datafile.get_mimetype())
    response['Content-Disposition'] = \
        '%s; filename="%s"' % (disposition, datafile.filename)
    return response

@experiment_access_required
def download_experiment(request, experiment_id, comptype):
    """
    takes string parameter "comptype" for compression method.
    Currently implemented: "zip" and "tar"
    """
    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # (tarfile count?)
    experiment = Experiment.objects.get(pk=experiment_id)

    if comptype == "tar":
        cmd = 'tar -C %s -c %s/' % (path.abspath(settings.FILE_STORE_PATH),
                                    str(experiment.id))
        # logger.info('TAR COMMAND: ' + cmd)
        response = HttpResponse(FileWrapper(subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=open(devnull, 'w'),
                    shell=True).stdout),
                                mimetype='application/x-tar')

        response['Content-Disposition'] = 'attachment; filename="experiment' \
            + str(experiment.id) + '-complete.tar"'
    elif comptype == "zip":
        cmd = 'cd %s; zip -r - %s' % (path.abspath(settings.FILE_STORE_PATH),
                                    str(experiment.id))
        # logger.info('TAR COMMAND: ' + cmd)
        response = HttpResponse(FileWrapper(subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=open(devnull, 'w'),
                    shell=True).stdout),
                                mimetype='application/zip')

        response['Content-Disposition'] = 'attachment; filename="experiment' \
            + str(experiment.id) + '-complete.zip"'
    else:
        return return_response_not_found(request)
    # response['Content-Length'] = fileSize + 5120
    return response


def download_datafiles(request):

    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # (tarfile count?)
    expid = request.POST['expid']
    fileString = ''

    comptype = "zip"
    if 'comptype' in request.POST:
        comptype = request.POST['comptype']

    if 'datafile' in request.POST:
        if len(request.POST.getlist('datafile')) > 500:
            comptype = "tar"

    if 'dataset' in request.POST:
        comptype = "tar" #todo quickfix, calc how many files

    # the following protocols can be handled by this module
    protocols = ['', 'file', 'tardis']
    known_protocols = len(protocols)
    if 'datafile' in request.POST or 'dataset' in request.POST:
        if (len(request.POST.getlist('datafile')) > 0 \
                or len(request.POST.getlist('dataset'))) > 0:

            datasets = request.POST.getlist('dataset')
            datafiles = request.POST.getlist('datafile')

            for dsid in datasets:
                for datafile in Dataset_File.objects.filter(dataset=dsid):
                    if has_datafile_access(request=request,
                                            dataset_file_id=datafile.id):
                        p = datafile.protocol
                        if not p in protocols:
                            protocols += [p]
                        absolute_filename = datafile.url.partition('//')[2]
                        if(datafile.url.partition('//')[0] == 'tardis:'):
                            #temp fix for old data
                            filepath = '%s/%s/%s' %\
                            (expid, str(datafile.dataset.id),
                                absolute_filename)

                            print filepath + "######"

                            try:
                                wrapper = FileWrapper(file(
                                    datafile.get_absolute_filepath()))\
                                #exists test. os.exists broken
                            except IOError:
                                print "OLD FILE DETECTED"
                                filepath = '%s/%s' % (expid, absolute_filename)

                            fileString += ('\"' + filepath + '\" ')
                            print fileString
                        else:
                            fileString += '\"%s/%s\" ' %\
                            (expid, absolute_filename)


            for dfid in datafiles:
                datafile = Dataset_File.objects.get(pk=dfid)
                if datafile.dataset.id in datasets:
                    continue
                if has_datafile_access(request=request,
                        dataset_file_id=datafile.id):
                    p = datafile.protocol
                    if not p in protocols:
                        protocols += [p]
                    absolute_filename = datafile.url.partition('//')[2]
                    if(datafile.url.partition('//')[0] == 'tardis:'):
                        #temp fix for old data
                        filepath = '\"%s/%s/%s\" ' %\
                        (expid, str(datafile.dataset.id),
                            absolute_filename)

                        print filepath + "######"

                        try:
                            wrapper = FileWrapper(file(
                                datafile.get_absolute_filepath()))\
                            #exists test. os.exists broken
                        except IOError:
                            print "OLD FILE DETECTED"
                            filepath = '\"%s/%s\" ' %\
                                       (expid, absolute_filename)

                        fileString += filepath
                        print fileString
                    else:
                        fileString += '\"%s/%s\" ' % (expid, absolute_filename)
        else:
            return return_response_not_found(request)

    elif 'url' in request.POST:
        if not len(request.POST.getlist('url')) == 0:
            comptype = "tar" #todo quickfix for zip error
            fileString = ""
            for url in request.POST.getlist('url'):
                url = urllib.unquote(url)
                raw_path = url.partition('//')[2]
                experiment_id = request.POST['expid']
                datafile = Dataset_File.objects.filter(url__endswith=raw_path,
                    dataset__experiment__id=experiment_id)[0]
                if has_datafile_access(request=request,
                                       dataset_file_id=datafile.id):
                    p = datafile.protocol
                    if not p in protocols:
                        protocols += [p]
                    absolute_filename = datafile.url.partition('//')[2]
                    if(datafile.url.partition('//')[0] == 'tardis:'):
                        # expects tardis: formatted stuff
                        # to not include dataset id

                        #temp fix for old data
                        filepath = '\"%s/%s/%s\" ' %\
                            (expid, str(datafile.dataset.id),
                            absolute_filename)

                        print filepath + "######"

                        try:
                            wrapper = FileWrapper(file(
                                datafile.get_absolute_filepath()))\
                            #exists test. os.exists broken
                        except IOError:
                            print "OLD FILE DETECTED"
                            filepath = '\"%s/%s\" ' %\
                                       (expid, absolute_filename)

                        fileString += ('\"' + filepath + '\" ')
                        print fileString
                    else:
                        fileString += '\"%s/%s\" ' % (expid, absolute_filename)
        else:
            return return_response_not_found(request)
    else:
        return return_response_not_found(request)

    # more than one external download location?
    if len(protocols) > known_protocols + 2:
        response = HttpResponseNotFound()
        response.write('<p>Different locations selected!</p>\n')
        response.write('Please limit your selection and try again.\n')
        return response

    # redirect request if another (external) download protocol was found
    elif len(protocols) == known_protocols + 1:
        from django.core.urlresolvers import reverse, resolve
        try:
            for module in settings.DOWNLOAD_PROVIDERS:
                if module[0] == protocols[3]:
                    url = reverse('%s.download_datafiles' % module[1])
                    view, args, kwargs = resolve(url)
                    kwargs['request'] = request
                    return view(*args, **kwargs)
        except:
            return return_response_not_found(request)

    else:
        # tarfile class doesn't work on large files being added and
        # streamed on the fly, so going command-line-o
        if not fileString:
            return return_response_error(request)

        if comptype == "tar":
            cmd = 'tar -C %s -c %s' % (settings.FILE_STORE_PATH,
                                       fileString)

            # logger.info(cmd)
            response = \
                HttpResponse(FileWrapper(subprocess.Popen(
                                                    cmd,
                                                    stdout=subprocess.PIPE,
                                                    stderr=open(devnull, 'w'),
                                                    shell=True).stdout),
                             mimetype='application/x-tar')
            response['Content-Disposition'] = \
                    'attachment; filename="experiment%s-selection.tar"' % expid
            return response
        else:
            cmd = 'cd %s; zip -r - %s' % (settings.FILE_STORE_PATH,
                                       fileString)
            # logger.info(cmd)
            response = \
                HttpResponse(FileWrapper(subprocess.Popen(
                                                    cmd,
                                                    stdout=subprocess.PIPE,
                                                    stderr=open(devnull, 'w'),
                                                    shell=True).stdout),
                             mimetype='application/zip')
            response['Content-Disposition'] = \
                    'attachment; filename="experiment%s-selection.zip"' % expid
            return response
