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
import os, platform, ctypes, stat, time, struct

try:
    import zlib # We may need its compression method
    crc32 = zlib.crc32
except ImportError:
    zlib = None
    crc32 = binascii.crc32
    
from itertools import chain
from tempfile import mkstemp, gettempdir, NamedTemporaryFile
from threading import Thread
from urllib2 import urlopen, URLError
from zipfile import ZipFile, ZipInfo, ZIP_STORED, ZIP_DEFLATED

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
        os.unlink(self.name)
        
class StreamableZipFile(ZipFile):
    def __init__(self, file, mode="r", compression=ZIP_STORED, allowZip64=False):
        ZipFile.__init__(self, file, mode, compression, allowZip64)
    
    def write(self, filename, arcname=None, compress_type=None):
        """Put the bytes from filename into the archive under the name
        arcname.  The file is written in strictly sequential fashion - no seeking."""
        
        # This code is a tweaked version of ZipFile.write ...
        # TODO: add an alternative version that works with a stream rather than a filename.
        if not self.fp:
            raise RuntimeError(
                  "Attempt to write to ZIP archive that was already closed")

        st = os.stat(filename)
        isdir = stat.S_ISDIR(st.st_mode)
        mtime = time.localtime(st.st_mtime)
        date_time = mtime[0:6]
        # Create ZipInfo instance to store file information
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        if isdir:
            arcname += '/'
        zinfo = ZipInfo(arcname, date_time)
        zinfo.external_attr = (st[0] & 0xFFFF) << 16L      # Unix attributes
        if compress_type is None:
            zinfo.compress_type = self.compression
        else:
            zinfo.compress_type = compress_type

        zinfo.file_size = st.st_size
        zinfo.flag_bits = 0x08                  # Use trailing data descriptor for file sizes and CRC 
        zinfo.header_offset = self.fp.tell()    # Start of header bytes

        self._writecheck(zinfo)
        self._didModify = True

        if isdir:
            zinfo.file_size = 0
            zinfo.compress_size = 0
            zinfo.CRC = 0
            self.filelist.append(zinfo)
            self.NameToInfo[zinfo.filename] = zinfo
            self.fp.write(zinfo.FileHeader())
            return

        with open(filename, "rb") as fp:
            # The CRC and sizes in the file header are zero ...
            zinfo.CRC = CRC = 0
            zinfo.compress_size = compress_size = 0
            zinfo.file_size = file_size = 0
            self.fp.write(zinfo.FileHeader())
            if zinfo.compress_type == ZIP_DEFLATED:
                cmpr = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                     zlib.DEFLATED, -15)
            else:
                cmpr = None
            while 1:
                buf = fp.read(1024 * 8)
                if not buf:
                    break
                file_size = file_size + len(buf)
                CRC = crc32(buf, CRC) & 0xffffffff
                if cmpr:
                    buf = cmpr.compress(buf)
                    compress_size = compress_size + len(buf)
                self.fp.write(buf)
        if cmpr:
            buf = cmpr.flush()
            compress_size = compress_size + len(buf)
            self.fp.write(buf)
            zinfo.compress_size = compress_size
        else:
            zinfo.compress_size = file_size
        # Write the data descriptor after the file containing the true sizes and CRC
        zinfo.CRC = CRC
        zinfo.file_size = file_size
        self.fp.write(struct.pack("<LLL", zinfo.CRC, zinfo.compress_size,
              zinfo.file_size))
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo
        
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
    return os.path.join(rootdir, str(df.dataset.id), df.filename)

def _get_datafile_details_for_archive(rootdir, datafiles):
    # It would be simplest to do this lazily.  But if we do that, we implicitly
    # passing the database context to the thread that will write the archive, and
    # that is a bit dodgy.  (It breaks in unit tests!)  Instead, we populate the
    # list eagerly, but with a file getter rather than the file itself.  If we
    # populate with actual File objects, we risk running out of file descriptors.
    return [(df.get_file_getter(), _get_filename(rootdir, df)) \
             for df in datafiles]

def _write_files_to_archive(write_func, files):
    for fileGetter, name in files:
        if not fileGetter:
            logger.debug('Skipping %s - no verified file is available.' % name)
            continue
        fileObj = fileGetter()
        if not fileObj:
            logger.debug('Skipping %s - file open failed.' % name)
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
            finally:
                fileObj.close()

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
            logger.debug('Completed tar archive size is %i' % os.stat(filename).st_size)
        except IOError as ex:
            logger.warn("I/O error({0}) while writing tar archive: {1}".format(e.errno, e.strerror))
            os.unlink(filename)
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
        try:
            zf = StreamableZipFile(filename, 'w', allowZip64=True)
            logger.debug('Writing zip archive to %s' % filename)
            _write_files_to_archive(zf.write, files)
            zf.close()
            logger.debug('Completed zip archive size is %i' % os.stat(filename).st_size)
        except IOError as ex:
            logger.warn("I/O error({0}) while writing zip archive: {1}".format(e.errno, e.strerror))
            os.unlink(filename)
        finally:
            zf.close()
    # Returns the function to do the actual writing
    return write_zip

def _estimate_archive_size(rootdir, datafiles, comptype):
    """
    produces an estimate of the size of the uncompressed file archive.  This is
    made based on the information we have to hand (i.e. the names and the notional file 
    sizes from the database.  We don't try to access the files themselves, as this
    potentially increases temporary disc space usage which is the resource we
    are primarily trying to protect at this point.
    """
    # TODO - include the implied entries for directories in the estimates.
    estimate = 0
    for df in datafiles:
        if comptype == "tar":
            # File header + file size with padding to 512
            estimate += 512 + ((int(df.get_size()) + 511) / 512) * 512
        elif comptype == "zip":
            name_length = len(_get_filename(rootdir, df))
            # local header + content + DD + file header
            estimate += (20 + name_length) + int(df.get_size()) + 8 + (46 + name_length) 
    if comptype == "tar":
         # Two records of zeros at the end.
         estimate += 1024
    elif comptype == "zip":
        # Central directory overheads
        estimate += 100 
    return estimate

def _get_free_temp_space():
    """ Return free space on the file system holding the temporary directory (in bytes)
    """
    sys_type = platform.system()
    if sys_type == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(gettempdir()), 
                                                   None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    elif sys_type == 'Darwin' or sys_type == 'DragonFly' or 'BSD' in sys_type:
        st = os.statvfs(gettempdir())
        return st.f_bfree * st.f_frsize
    elif sys_type == 'Linux':
        st = os.statvfs(gettempdir())
        return st.f_bfree * st.f_bsize
    else:
        raise RuntimeError('Unsupported / unexpected platform type: %s' % sys_type)

def _check_download_limits(rootdir, datafiles, comptype):
    estimate = _estimate_archive_size(rootdir, datafiles, comptype)
    available = _get_free_temp_space()
    logger.debug('Estimated archive size: %i, available tempfile space %i' % (estimate, available))
    if settings.DOWNLOAD_ARCHIVE_SIZE_LIMIT > 0 and estimate > settings.DOWNLOAD_ARCHIVE_SIZE_LIMIT:
        return 'Download archive size exceeds the allowed limit: try a smaller download'
    elif estimate > available + settings.DOWNLOAD_SPACE_SAFETY_MARGIN:
        return 'Insufficient temp file space available to create the archive:' \
                ' try a smaller download, or try again later'
    else:
        return None

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
    rootdir = str(experiment_id)
    msg = _check_download_limits(rootdir, datafiles, comptype)
    if msg:
        return return_response_not_found(request)

    if comptype == "tar":
        reader = StreamingFile(_write_tar_func(rootdir, datafiles),
                               asynchronous_file_creation=True)

        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/x-tar')
        response['Content-Disposition'] = 'attachment; filename="experiment' \
            + rootdir + '-complete.tar"'
    elif comptype == "zip":
        reader = StreamingFile(_write_zip_func(rootdir, datafiles),
                               asynchronous_file_creation=True)
        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/zip')

        response['Content-Disposition'] = 'attachment; filename="experiment' \
            + rootdir + '-complete.zip"'
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
    
    rootdir = 'datasets'
    msg = _check_download_limits(rootdir, df_set, comptype)
    if msg:
        return return_response_not_found(request)

    # Handle missing experiment ID - only need it for naming
    try:
        expid = request.POST['expid']
    except KeyError:
        expid = iter(df_set).next().dataset.get_first_experiment().id

    if comptype == "tar":
        reader = StreamingFile(_write_tar_func(rootdir, df_set),
                               asynchronous_file_creation=True)
        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/x-tar')
        response['Content-Disposition'] = \
                'attachment; filename="experiment%s-selection.tar"' % expid
    elif comptype == "zip":
        reader = StreamingFile(_write_zip_func(rootdir, df_set),
                               asynchronous_file_creation=True)
        response = HttpResponse(FileWrapper(reader),
                                mimetype='application/zip')    
        response['Content-Disposition'] = \
                'attachment; filename="experiment%s-selection.zip"' % expid
    else:
        response = return_response_not_found(request)
    return response

        