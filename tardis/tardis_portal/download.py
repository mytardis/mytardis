# -*- coding: utf-8 -*-
"""
download.py

.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>
.. moduleauthor::  Grischa Meyer <grischa.meyer@monash.edu>

"""
import logging
import urllib
import os
import cStringIO as StringIO
import time

try:
    import zlib  # We may need its compression method
    crc32 = zlib.crc32
except ImportError:
    zlib = None
    import binascii
    crc32 = binascii.crc32

from itertools import chain
import tarfile
from tarfile import TarFile
import gzip
import io

from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.conf import settings
from django.utils.dateformat import format as dateformatter
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.decorators import login_required

from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import DataFile
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.auth.decorators import has_datafile_download_access
from tardis.tardis_portal.auth.decorators import experiment_download_required
from tardis.tardis_portal.auth.decorators import dataset_download_required
from tardis.tardis_portal.shortcuts import render_error_message
from tardis.tardis_portal.views import return_response_not_found, \
    return_response_error

logger = logging.getLogger(__name__)

DEFAULT_ORGANIZATION = settings.DEFAULT_ARCHIVE_ORGANIZATION


def _create_download_response(request, datafile_id, disposition='attachment'):  # too complex # noqa
    # Get datafile (and return 404 if absent)
    try:
        datafile = DataFile.objects.get(pk=datafile_id)
    except DataFile.DoesNotExist:
        return return_response_not_found(request)
    # Check users has access to datafile
    if not has_datafile_download_access(request=request,
                                        datafile_id=datafile.id):
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
        verified_only = True
        # Query parameter to allow download of unverified files
        ignore_verif = request.GET.get('ignore_verification_status', '0')
        # Ensure ignore_verification_status=0 etc works as expected
        # a bare ?ignore_verification_status is True
        if ignore_verif.lower() in [u'', u'1', u'true']:
            verified_only = False

        # Get file object for datafile
        file_obj = datafile.get_file(verified_only=verified_only)
        if not file_obj:
            # If file path doesn't resolve, return not found
            if verified_only:
                return render_error_message(request,
                                            "File is unverified, "
                                            "please try again later.",
                                            status=503)
            else:
                return return_response_not_found(request)
        wrapper = FileWrapper(file_obj, blksize=65535)
        response = StreamingHttpResponse(wrapper,
                                         content_type=datafile.get_mimetype())
        response['Content-Disposition'] = \
            '%s; filename="%s"' % (disposition, datafile.filename)
        return response
    except IOError:
        # If we can't read the file, return not found
        return return_response_not_found(request)
    except ValueError:  # raised when replica not verified TODO: custom excptn
        redirect = request.META.get('HTTP_REFERER',
                                    'http://%s/' %
                                    request.META.get('HTTP_HOST'))
        message = """The file you are trying to access has not yet been
                     verified. Verification is an automated background process.
                     Please try again later or contact the system
                     administrator if the issue persists."""
        message = ' '.join(message.split())  # removes spaces
        redirect = redirect + '#error:' + message
        return HttpResponseRedirect(redirect)


def view_datafile(request, datafile_id):
    return _create_download_response(request, datafile_id, 'inline')


def download_datafile(request, datafile_id):
    return _create_download_response(request, datafile_id)


__mapper_makers = None


def get_download_organizations():
    return _get_mapper_makers().keys()


def _get_mapper_makers():
    global __mapper_makers
    if not __mapper_makers:
        __mapper_makers = {}
        mappers = getattr(settings, 'ARCHIVE_FILE_MAPPERS', [])
        for (organization, mapper_desc) in mappers.items():
            mapper_fn = _safe_import(mapper_desc[0])
            if len(mapper_desc) >= 2:
                kwarg = mapper_desc[1]
            else:
                kwarg = {}

            def mapper_maker_maker(kwarg):
                def mapper_maker(rootdir):
                    myKwarg = dict(kwarg)
                    myKwarg['rootdir'] = rootdir

                    def mapper(datafile):
                        return mapper_fn(datafile, **myKwarg)
                    return mapper
                return mapper_maker
            __mapper_makers[organization] = mapper_maker_maker(kwarg)
    return __mapper_makers


def _safe_import(path):
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured('%s isn\'t an archive mapper' % path)
    mapper_module, mapper_fname = path[:dot], path[dot + 1:]
    try:
        mod = import_module(mapper_module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing mapper %s: "%s"' %
                                   (mapper_module, e))
    try:
        return getattr(mod, mapper_fname)
    except AttributeError:
        raise ImproperlyConfigured(
            'Mapper module "%s" does not define a "%s" function' %
            (mapper_module, mapper_fname))


def _make_mapper(organization, rootdir):
    if organization == 'classic':
        return classic_mapper(rootdir)
    else:
        mapper_makers = _get_mapper_makers()
        mapper_maker = mapper_makers.get(organization)
        if mapper_maker:
            return mapper_maker(rootdir)
        else:
            return None


def classic_mapper(rootdir):
    def _get_filename(df):
        return os.path.join(rootdir, str(df.dataset.id), df.filename)
    return _get_filename


def _get_datafile_details_for_archive(mapper, datafiles):
    # It would be simplest to do this lazily.  But if we do that, we implicitly
    # passing the database context to the thread that will write the archive,
    # and that is a bit dodgy.  (It breaks in unit tests!)  Instead, we
    # populate the list eagerly, but with a file getter rather than the file
    # itself.  If we populate with actual File objects, we risk running out
    # of file descriptors.
    res = []
    for df in datafiles:
        mapped_pathname = mapper(df)
        if mapped_pathname:
            res.append((df, mapper(df)))
    return res


########### NEW DOWNLOAD ##############
class UncachedTarStream(TarFile):
    '''
    Stream files into a compressed tar stream on the fly
    '''

    def __init__(self, mapped_file_objs, filename, do_gzip=False,
                 buffersize=2*65536, comp_level=6, http_buffersize=65535):
        self.errors = 'strict'
        self.pax_headers = {}
        self.mode = 'w'
        self.closed = False
        self.members = []
        self._loaded = False
        self.offset = 0
        self.inodes = {}
        self._loaded = True
        self.mapped_file_objs = mapped_file_objs
        filenum = len(mapped_file_objs)
        self.tarinfos = [None] * filenum
        self.tarinfo_bufs = [None] * filenum
        self.filename = filename
        self.buffersize = buffersize
        self.http_buffersize = http_buffersize
        self.do_gzip = do_gzip
        if do_gzip:
            self.binary_buffer = io.BytesIO()
            self.gzipfile = gzip.GzipFile(bytes(filename), 'w',
                                          comp_level, self.binary_buffer)
        else:
            self.tar_size = self.compute_size()

    def compute_size(self):
        total_size = 0
        for num, fobj in enumerate(self.mapped_file_objs):
            df, name = fobj
            tarinfo = self.tarinfo_for_df(df, name)
            self.tarinfos[num] = tarinfo
            tarinfo_buf = tarinfo.tobuf(self.format, self.encoding, self.errors)
            self.tarinfo_bufs[num] = tarinfo_buf
            total_size += len(tarinfo_buf)
            size = int(tarinfo.size)
            blocks, remainder = divmod(size, tarfile.BLOCKSIZE)
            if remainder > 0:
                blocks += 1
            total_size += blocks * tarfile.BLOCKSIZE
        blocks, remainder = divmod(total_size, tarfile.RECORDSIZE)
        if remainder > 0:
            blocks += 1
        total_size = blocks * tarfile.RECORDSIZE
        return total_size

    def tarinfo_for_df(self, df, name):
        tarinfo = self.tarinfo(name)
        tarinfo.size = int(df.get_size())
        mtime = None
        dj_mtime = df.modification_time
        if dj_mtime is not None:
            mtime = dateformatter(dj_mtime, 'U')
        else:
            try:
                fileobj = df.file_object
                mtime = os.fstat(fileobj.fileno()).st_mtime
            except:
                raise Exception('cannot read size for downloads')
        if mtime is None:
            mtime = time.time()
        tarinfo.mtime = mtime
        return tarinfo

    def compress(self, buf):
        self.gzipfile.write(buf)
        self.gzipfile.flush()
        self.binary_buffer.seek(0)
        result = self.binary_buffer.read()
        self.binary_buffer.seek(0)
        self.binary_buffer.truncate()
        return result

    def prepare_output(self, uc_buf, remainder):
        if self.do_gzip:
            result_buf = self.compress(uc_buf)
        else:
            result_buf = uc_buf
        if remainder is not None:
            result_buf = ''.join([remainder, result_buf])
        stream_buffers = []
        while len(result_buf) >= self.http_buffersize:
            stream_buffers.append(result_buf[:self.http_buffersize])
            result_buf = result_buf[self.http_buffersize:]
        return stream_buffers, result_buf

    def close_gzip(self):
        self.gzipfile.close()
        self.binary_buffer.seek(0)
        result = self.binary_buffer.read()
        self.binary_buffer.seek(0)
        self.binary_buffer.truncate()
        print len(result)
        return result

    def make_tar(self):  # noqa
        '''
        main tar generator. until python 3 needs to be in one function
        because 'yield's don't bubble up.
        '''
        remainder_buf = None
        for num, fobj in enumerate(self.mapped_file_objs):
            df, name = fobj
            fileobj = df.file_object
            self._check('aw')
            tarinfo = self.tarinfos[num]
            buf = self.tarinfo_bufs[num]
            stream_buffers, remainder_buf = self.prepare_output(
                buf,
                remainder_buf)
            for stream_buf in stream_buffers:
                yield stream_buf
            self.offset += len(buf or '')
            if tarinfo.isreg():
                if tarinfo.size == 0:
                    continue
                # split into file read buffer sized chunks
                blocks, remainder = divmod(tarinfo.size, self.buffersize)
                for b in xrange(blocks):
                    buf = fileobj.read(self.buffersize)
                    if len(buf) < self.buffersize:
                        raise IOError("end of file reached")
                    # send in http_buffersize sized chunks
                    stream_buffers, remainder_buf = self.prepare_output(
                        buf, remainder_buf)
                    for stream_buf in stream_buffers:
                        yield stream_buf
                # in case the file has remaining read bytes
                if remainder != 0:
                    buf = fileobj.read(remainder)
                    if len(buf) < remainder:
                        raise IOError("end of file reached")
                    # send remaining file data
                    stream_buffers, remainder_buf = self.prepare_output(
                        buf, remainder_buf)
                    for stream_buf in stream_buffers:
                        yield stream_buf
                blocks, remainder = divmod(tarinfo.size, tarfile.BLOCKSIZE)
                if remainder > 0:
                    buf = (tarfile.NUL * (tarfile.BLOCKSIZE - remainder))
                    stream_buffers, remainder_buf = self.prepare_output(
                        buf, remainder_buf)
                    for stream_buf in stream_buffers:
                        yield stream_buf
                    blocks += 1
                self.offset += blocks * tarfile.BLOCKSIZE
            fileobj.close()
        # fill up the end with zero-blocks
        # (like option -b20 for tar does)
        blocks, remainder = divmod(self.offset, tarfile.RECORDSIZE)
        if remainder > 0:
            buf = tarfile.NUL * (tarfile.RECORDSIZE - remainder)
            stream_buffers, remainder_buf = self.prepare_output(
                buf, remainder_buf)
            for stream_buf in stream_buffers:
                yield stream_buf
        if remainder_buf and len(remainder_buf) > 0:
            yield remainder_buf
        if self.do_gzip:
            yield self.close_gzip()

    def get_response(self):
        if self.do_gzip:
            content_type = 'application/x-gzip'
            content_length = None
            self.filename += '.gz'
        else:
            content_type = 'application/x-tar'
            content_length = self.tar_size
        response = StreamingHttpResponse(self.make_tar(),
                                         content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
                                          self.filename
        response['X-Accel-Buffering'] = 'no'
        if content_length is not None:
            response['Content-Length'] = content_length
        return response


def _streaming_downloader(request, datafiles, rootdir, filename,
                          comptype='tgz', organization=DEFAULT_ORGANIZATION):
    '''
    private function to be called by wrappers
    creates download response with given files and names
    '''
    mapper = _make_mapper(organization, rootdir)
    if not mapper:
        return render_error_message(
            request, 'Unknown download organization: %s' % organization,
            status=400)
    try:
        files = _get_datafile_details_for_archive(mapper, datafiles)
        tfs = UncachedTarStream(
            files,
            filename=filename,
            do_gzip=comptype != 'tar')
        return tfs.get_response()
    except ValueError:  # raised when replica not verified TODO: custom excptn
        redirect = request.META.get('HTTP_REFERER',
                                    'http://%s/' %
                                    request.META.get('HTTP_HOST'))
        message = """The experiment you are trying to access has not yet been
                     verified completely.
                     Verification is an automated background process.
                     Please try again later or contact the system
                     administrator if the issue persists."""
        message = ' '.join(message.split())  # removes spaces
        redirect = redirect + '#error:' + message
        return HttpResponseRedirect(redirect)


@experiment_download_required
def streaming_download_experiment(request, experiment_id, comptype='tgz',
                                  organization=DEFAULT_ORGANIZATION):
    experiment = Experiment.objects.get(id=experiment_id)
    rootdir = experiment.title.replace(' ', '_')
    filename = '%s-complete.tar' % rootdir

    datafiles = DataFile.objects.filter(
        dataset__experiments__id=experiment_id)
    return _streaming_downloader(request, datafiles, rootdir, filename,
                                 comptype, organization)


@dataset_download_required
def streaming_download_dataset(request, dataset_id, comptype='tgz',
                               organization=DEFAULT_ORGANIZATION):
    dataset = Dataset.objects.get(id=dataset_id)
    rootdir = dataset.description.replace(' ', '_')
    filename = '%s-complete.tar' % rootdir

    datafiles = DataFile.objects.filter(dataset=dataset)
    return _streaming_downloader(request, datafiles, rootdir, filename,
                                 comptype, organization)


def streaming_download_datafiles(request):  # too complex # noqa
    """
    takes string parameter "comptype" for compression method.
    Currently implemented: "tgz" and "tar"
    The datafiles to be downloaded are selected using "datafile", "dataset"
    or "url" parameters.  An "expid" parameter may be supplied for use in
    the download archive name.  If "url" is used, the "expid" parameter
    is also used to limit the datafiles to be downloaded to a given experiment.
    """
    # Create the HttpResponse object with the appropriate headers.
    # TODO: handle no datafile, invalid filename, all http links
    # TODO: intelligent selection of temp file versus in-memory buffering.
    logger.error('In download_datafiles !!')
    comptype = getattr(settings, 'DEFAULT_ARCHIVE_FORMATS', ['tar'])[0]
    organization = getattr(settings, 'DEFAULT_ARCHIVE_ORGANIZATION', 'classic')
    if 'comptype' in request.POST:
        comptype = request.POST['comptype']
    if 'organization' in request.POST:
        organization = request.POST['organization']

    if 'datafile' in request.POST or 'dataset' in request.POST:
        if (len(request.POST.getlist('datafile')) > 0
                or len(request.POST.getlist('dataset'))) > 0:

            datasets = request.POST.getlist('dataset')
            datafiles = request.POST.getlist('datafile')

            # Generator to produce datafiles from dataset id
            def get_dataset_datafiles(dsid):
                for datafile in DataFile.objects.filter(dataset=dsid):
                    if has_datafile_download_access(
                            request=request, datafile_id=datafile.id):
                        yield datafile

            # Generator to produce datafile from datafile id
            def get_datafile(dfid):
                datafile = DataFile.objects.get(pk=dfid)
                if has_datafile_download_access(request=request,
                                                datafile_id=datafile.id):
                    yield datafile

            # Take chained generators and turn them into a set of datafiles
            df_set = set(chain(chain.from_iterable(map(get_dataset_datafiles,
                                                       datasets)),
                               chain.from_iterable(map(get_datafile,
                                                       datafiles))))
        else:
            return render_error_message(
                request,
                'No Datasets or Datafiles were selected for downloaded',
                status=404)

    elif 'url' in request.POST:
        if len(request.POST.getlist('url')) != 0:
            return render_error_message(
                request,
                'No Datasets or Datafiles were selected for downloaded',
                status=404)

        for url in request.POST.getlist('url'):
            url = urllib.unquote(url)
            raw_path = url.partition('//')[2]
            experiment_id = request.POST['expid']
            datafile = DataFile.objects.filter(
                url__endswith=raw_path,
                dataset__experiment__id=experiment_id)[0]
            if has_datafile_download_access(request=request,
                                            datafile_id=datafile.id):
                df_set = set([datafile])
    else:
        return render_error_message(
            request, 'No Datasets or Datafiles were selected for downloaded',
            status=404)

    logger.info('Files for archive command: %s' % df_set)

    if len(df_set) == 0:
        return render_error_message(
            request,
            'You do not have download access for any of the '
            'selected Datasets or Datafiles ',
            status=403)

    try:
        expid = request.POST['expid']
        experiment = Experiment.objects.get(id=expid)
    except (KeyError, Experiment.DoesNotExist):
        experiment = iter(df_set).next().dataset.get_first_experiment()

    filename = '%s-selection.tar' % experiment.title.replace(' ', '_')
    rootdir = '%s-selection' % experiment.title.replace(' ', '_')
    return _streaming_downloader(request, df_set, rootdir, filename,
                                 comptype, organization)


@login_required
def download_api_key(request):
    user = request.user
    api_key_file = StringIO.StringIO()
    api_key_file.write("ApiKey {0}:{1}".format(user, user.api_key.key))
    api_key_file.seek(0)
    response = StreamingHttpResponse(FileWrapper(api_key_file),
                                     content_type='text/plain')
    response['Content-Disposition'] = \
        'attachment; filename="{0}.key"' .format(user)
    return response
