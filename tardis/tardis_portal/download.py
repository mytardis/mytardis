# -*- coding: utf-8 -*-

"""
download.py

.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>

"""
import logging
import shutil
import subprocess
import urllib
from itertools import chain
from tempfile import mkstemp, NamedTemporaryFile
from threading import Thread
from urllib2 import urlopen, URLError

from os import path, devnull, unlink

from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotFound
from django.conf import settings

from tardis.tardis_portal.models import *
from tardis.tardis_portal.auth.decorators import *
from tardis.tardis_portal.views import return_response_not_found, \
    return_response_error

logger = logging.getLogger(__name__)

class StreamingFile:

    def __init__(self, writer_callable, asynchronous_file_creation=False):
        # Caution, only use 'asynchronous_file_creation=True' if the 
        # writer_callable outputs the file strictly sequentially.  If it seeks
        # backwards to back-fill details (like ZipFile does!), this can cause 
        # a data race and can result in a corrupted download.
        _, self.name = mkstemp()
        self.asynchronous = asynchronous_file_creation
        if asynchronous_file_creation:
            self.runnable = writer_callable
            self.thread = Thread(target=self)
            self.thread.start()
        else:
            writer_callable(self.name)
        self.reader = open(self.name, 'rb')

    def __call__(self):
        self.runnable(self.name)

    def read(self, size=1):
        def read_file(size):
            return self.reader.read(size)

        remaining_bytes = size
        buf = ''
        if self.asynchronous:
            while self.thread.is_alive() and remaining_bytes > 0:
                from time import sleep
                sleep(0.01)
                read_bytes = read_file(remaining_bytes)
                buf += read_bytes
                remaining_bytes -= len(read_bytes)

        if remaining_bytes > 0:
            buf += read_file(remaining_bytes)

        return buf

    def close(self):
        self.reader.close()
        unlink(self.name)

def _create_download_response(request, datafile_id, disposition='attachment'):
    # Get datafile (and return 404 if absent)
    try:
        datafile = Dataset_File.objects.get(pk=datafile_id)
    except Dataset_File.DoesNotExist:
        return return_response_not_found(request)
    # Check users has access to datafile
    if not has_datafile_download_access(request=request,
                                        dataset_file_id=datafile.id):
        return return_response_error(request)
    # Send an image that can be seen in the browser
    if disposition == 'inline' and datafile.is_image():
        from tardis.tardis_portal.iiif import download_image
        args = (request, datafile.id, 'full', 'full', '0', 'native')
        # Send unconverted image if web-compatible
        if datafile.get_mimetype() in ('image/gif', 'image/jpeg', 'image/png'):
            return download_image(*args)
        # Send converted image
        return download_image(*args, format='png')
    # Send local file
    try:
        # Get file object for datafile
        file_obj = datafile.get_file()
        if not file_obj:
            # If file path doesn't resolve, return not found
            return return_response_not_found(request)
        wrapper = FileWrapper(file_obj)
        response = HttpResponse(wrapper,
                                mimetype=datafile.get_mimetype())
        response['Content-Disposition'] = \
            '%s; filename="%s"' % (disposition, datafile.filename)
        return response
    except IOError:
        # If we can't read the file, return not found
        return return_response_not_found(request)

def view_datafile(request, datafile_id):
    return _create_download_response(request, datafile_id, 'inline')

def download_datafile(request, datafile_id):
    return _create_download_response(request, datafile_id)

def _get_filename(rootdir, df):
    return path.join(rootdir, str(df.dataset.id), df.filename)

def _get_datafile_details_for_archive(rootdir, datafiles):
    return ((df.get_file(), _get_filename(rootdir, df)) \
             for df in datafiles)

def _write_files_to_archive(write_func, files):
    for fileObj, name in files:
        if not fileObj:
            logger.debug('Skipping %s - no file available.' % name)
            continue
        with NamedTemporaryFile(prefix='mytardis_tmp_dl_') as fdst:
            try:
                # Copy url to destination file
                shutil.copyfileobj(fileObj, fdst)
                # Flush the file so we can read from it properly
                fdst.flush()
                # Write file
                write_func(fdst.name, name)
            except URLError:
                logger.warn("Unable to fetch %s for archive download." % name)

def _write_tar_func(rootdir, datafiles):
    logger.debug('Getting files to write to archive')
    # Resolve url and name for the files
    files = _get_datafile_details_for_archive(rootdir, datafiles)
    # Define the function
    def write_tar(filename):
        from tarfile import TarFile
        try:
            tf = TarFile(filename, 'w')
            logger.debug('Writing tar archive to %s' % filename)
            _write_files_to_archive(tf.add, files)
            tf.close()
        except IOError as ex:
            logger.warn("I/O error({0}) while writing tar archive: {1}".format(e.errno, e.strerror))
            unlink(filename)
        finally:
            tf.close()
    # Returns the function to do the actual writing
    return write_tar

def _write_zip_func(rootdir, datafiles):
    logger.debug('Getting files to write to archive')
    # Resolve url and name for the files
    files = _get_datafile_details_for_archive(rootdir, datafiles)
    # Define the function
    def write_zip(filename):
        from zipfile import ZipFile
        try:
            zf = ZipFile(filename, 'w', allowZip64=True)
            logger.debug('Writing zip archive to %s' % filename)
            _write_files_to_archive(zf.write, files)
            zf.close()
        except IOError as ex:
            logger.warn("I/O error({0}) while writing zip archive: {1}".format(e.errno, e.strerror))
            unlink(filename)
        finally:
            zf.close()
    # Returns the function to do the actual writing
    return write_zip


@experiment_download_required
def download_experiment(request, experiment_id, comptype):
    """
    takes string parameter "comptype" for compression method.
    Currently implemented: "zip" and "tar"
    """
    # TODO: do size estimation, check available temp filespace, check download limits 
    # TODO: intelligent selection of temp file versus in-memory buffering.
    datafiles = Dataset_File.objects\
        .filter(dataset__experiments__id=experiment_id)

    if comptype == "tar":
        reader = StreamingFile(_write_tar_func(str(experiment_id), datafiles),
                               asynchronous_file_creation=True)

        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/x-tar')
        response['Content-Disposition'] = 'attachment; filename="experiment' \
            + str(experiment_id) + '-complete.tar"'
    elif comptype == "zip":
        reader = StreamingFile(_write_zip_func(str(experiment_id), datafiles))
        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/zip')

        response['Content-Disposition'] = 'attachment; filename="experiment' \
            + str(experiment_id) + '-complete.zip"'
    else:
        response = return_response_not_found(request)
    return response


def download_datafiles(request):

    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # TODO: do size estimation, check available temp filespace, check download limits 
    # TODO: intelligent selection of temp file versus in-memory buffering.
    comptype = "zip"
    if 'comptype' in request.POST:
        comptype = request.POST['comptype']

    if 'datafile' in request.POST or 'dataset' in request.POST:
        if (len(request.POST.getlist('datafile')) > 0 \
                or len(request.POST.getlist('dataset'))) > 0:

            datasets = request.POST.getlist('dataset')
            datafiles = request.POST.getlist('datafile')

            # Generator to produce datafiles from dataset id
            def get_dataset_datafiles(dsid):
                for datafile in Dataset_File.objects.filter(dataset=dsid):
                    if has_datafile_download_access(request=request,
                                                    dataset_file_id=datafile.id):
                        yield datafile


            # Generator to produce datafile from datafile id
            def get_datafile(dfid):
                datafile = Dataset_File.objects.get(pk=dfid)
                if has_datafile_download_access(request=request,
                                                dataset_file_id=datafile.id):
                    yield datafile

            # Take chained generators and turn them into a set of datafiles
            df_set = set(chain(chain.from_iterable(map(get_dataset_datafiles,
                                                       datasets)),
                               chain.from_iterable(map(get_datafile,
                                                       datafiles))))
        else:
            return return_response_not_found(request)

    elif 'url' in request.POST:
        if not len(request.POST.getlist('url')) == 0:
            return return_response_not_found(request)

        for url in request.POST.getlist('url'):
            url = urllib.unquote(url)
            raw_path = url.partition('//')[2]
            experiment_id = request.POST['expid']
            datafile = Dataset_File.objects.filter(url__endswith=raw_path,
                dataset__experiment__id=experiment_id)[0]
            if has_datafile_download_access(request=request,
                                            dataset_file_id=datafile.id):
                df_set = set([datafile])
    else:
        return return_response_not_found(request)

    logger.info('Files for archive command: %s' % df_set)

    if len(df_set) == 0:
        return return_response_error(request)

    # Handle missing experiment ID - only need it for naming
    try:
        expid = request.POST['expid']
    except KeyError:
        expid = iter(df_set).next().dataset.get_first_experiment().id

    if comptype == "tar":
        reader = StreamingFile(_write_tar_func('datasets', df_set),
                               asynchronous_file_creation=True)
        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/x-tar')
        response['Content-Disposition'] = \
                'attachment; filename="experiment%s-selection.tar"' % expid
    elif comptype == "zip":
        reader = StreamingFile(_write_zip_func('datasets', df_set))
        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/zip')    
        response['Content-Disposition'] = \
                'attachment; filename="experiment%s-selection.zip"' % expid
    else:
        response = return_response_not_found(request)
    return response

        