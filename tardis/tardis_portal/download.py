# pylint: disable=W0640
# -*- coding: utf-8 -*-
"""
download.py

.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  Ulrich Felzmann <ulrich.felzmann@versi.edu.au>
.. moduleauthor::  Grischa Meyer <grischa.meyer@monash.edu>

"""
import logging
import os
import time
import urllib
from importlib import import_module

try:
    import zlib  # We may need its compression method

    crc32 = zlib.crc32
except ImportError:
    zlib = None
    import binascii

    crc32 = binascii.crc32

import gzip
import io
import tarfile
from itertools import chain
from tarfile import TarFile
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import StreamingHttpResponse
from django.utils.dateformat import format as dateformatter

from tardis.analytics.tracker import IteratorTracker

from .auth.decorators import (
    dataset_download_required,
    experiment_download_required,
    has_download_access,
)
from .models import DataFile, DataFileObject, Dataset, Experiment
from .shortcuts import (
    redirect_back_with_error,
    render_error_message,
    return_response_error,
    return_response_not_found,
)
from .util import get_filesystem_safe_dataset_name, get_filesystem_safe_experiment_name

logger = logging.getLogger(__name__)

DEFAULT_ORGANIZATION = settings.DEFAULT_PATH_MAPPER


def _create_download_response(
    request, datafile_id, disposition="attachment"
):  # too complex # noqa
    # Get datafile (and return 404 if absent)
    try:
        datafile = DataFile.objects.get(pk=datafile_id)
    except DataFile.DoesNotExist:
        return return_response_not_found(request)
    # Check users has access to datafile
    if not has_download_access(request=request, obj_id=datafile.id, ct_type="datafile"):
        return return_response_error(request)

    # Log file download event
    if getattr(settings, "ENABLE_EVENTLOG", False):
        from tardis.apps.eventlog.utils import log

        log(
            action="DOWNLOAD_DATAFILE",
            extra={"id": datafile.id, "type": "single"},
            request=request,
        )

    # Send an image that can be seen in the browser
    if disposition == "inline" and datafile.is_image():
        from .iiif import download_image

        args = (request, datafile.id, "full", "full", "0", "native")
        # Send unconverted image if web-compatible
        if datafile.get_mimetype() in ("image/gif", "image/jpeg", "image/png"):
            return download_image(*args)
        # Send converted image
        return download_image(*args, format="png")
    # Send local file
    try:
        verified_only = True
        # Query parameter to allow download of unverified files
        ignore_verif = request.GET.get("ignore_verification_status", "0")
        # Ensure ignore_verification_status=0 etc works as expected
        # a bare ?ignore_verification_status is True
        if ignore_verif.lower() in ["", "1", "true"]:
            verified_only = False

        # Get file object for datafile
        file_obj = datafile.get_file(verified_only=verified_only)
        if not file_obj:
            # If file path doesn't resolve, return not found
            if verified_only:
                return render_error_message(
                    request,
                    "File is unverified, please try again later.",
                    status=503,
                )
            return return_response_not_found(request)
        wrapper = FileWrapper(file_obj, blksize=65535)
        response = StreamingHttpResponse(wrapper, content_type=datafile.get_mimetype())
        response["Content-Disposition"] = '%s; filename="%s"' % (
            disposition,
            datafile.filename,
        )
        return response
    except IOError:
        # If we can't read the file, return not found
        return return_response_not_found(request)
    except ValueError:  # raised when replica not verified TODO: custom excptn
        message = """The file you are trying to access has not yet been
                     verified. Verification is an automated background process.
                     Please try again later or contact the system
                     administrator if the issue persists."""
        message = " ".join(message.split())  # removes spaces
        return redirect_back_with_error(request, message)


def view_datafile(request, datafile_id):
    return _create_download_response(request, datafile_id, "inline")


def download_datafile(request, datafile_id):
    return _create_download_response(request, datafile_id)


__mapper_makers = None


def get_download_organizations():
    return _get_mapper_makers().keys()


def _get_mapper_makers():
    global __mapper_makers
    if not __mapper_makers:
        __mapper_makers = {}
        mappers = getattr(settings, "DOWNLOAD_PATH_MAPPERS", {})
        for organization, mapper_desc in mappers.items():
            mapper_fn = _safe_import(mapper_desc[0])
            if len(mapper_desc) >= 2:
                kwarg = mapper_desc[1]
            else:
                kwarg = {}

            def mapper_maker_maker(kwarg):
                def mapper_maker(rootdir):
                    myKwarg = dict(kwarg)
                    myKwarg["rootdir"] = rootdir

                    def mapper(datafile):
                        # TODO: remove this complex code. warning silenced for
                        # now because no time to investigate
                        return mapper_fn(datafile, **myKwarg)

                    return mapper

                return mapper_maker

            __mapper_makers[organization] = mapper_maker_maker(kwarg)
    return __mapper_makers


def _safe_import(path):
    try:
        dot = path.rindex(".")
    except ValueError:
        raise ImproperlyConfigured("%s isn't an archive mapper" % path)
    mapper_module, mapper_fname = path[:dot], path[dot + 1 :]
    try:
        mod = import_module(mapper_module)
    except ImportError as e:
        raise ImproperlyConfigured(
            'Error importing mapper %s: "%s"' % (mapper_module, e)
        )
    try:
        return getattr(mod, mapper_fname)
    except AttributeError:
        raise ImproperlyConfigured(
            'Mapper module "%s" does not define a "%s" function'
            % (mapper_module, mapper_fname)
        )


def make_mapper(organization, rootdir):
    if organization == "classic":
        return classic_mapper(rootdir)
    mapper_makers = _get_mapper_makers()
    mapper_maker = mapper_makers.get(organization)
    if mapper_maker:
        return mapper_maker(rootdir)
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


class UncachedTarStream(TarFile):
    """
    Stream files into a compressed tar stream on the fly
    """

    def __init__(
        self,
        mapped_file_objs,
        filename,
        do_gzip=False,
        buffersize=2 * 65536,
        comp_level=6,
        http_buffersize=65535,
    ):
        self.errors = "strict"
        self.pax_headers = {}
        self.mode = "w"
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
            self.gzipfile = gzip.GzipFile(
                bytes(filename), "w", comp_level, self.binary_buffer
            )
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
        try:
            dj_mtime = df.modification_time or df.get_preferred_dfo().modified_time
        except Exception as e:
            dj_mtime = None
            logger.debug(
                "cannot read m_time for file id" " %d, exception %s" % (df.id, str(e))
            )
        if dj_mtime is not None:
            tarinfo.mtime = float(dateformatter(dj_mtime, "U"))
        else:
            tarinfo.mtime = time.time()
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
            result_buf = b"".join([remainder, result_buf])
        stream_buffers = []
        while len(result_buf) >= self.http_buffersize:
            stream_buffers.append(result_buf[: self.http_buffersize])
            result_buf = result_buf[self.http_buffersize :]
        return stream_buffers, result_buf

    def close_gzip(self):
        self.gzipfile.close()
        self.binary_buffer.seek(0)
        result = self.binary_buffer.read()
        self.binary_buffer.seek(0)
        self.binary_buffer.truncate()
        return result

    def make_tar(self):  # noqa
        """
        main tar generator. until python 3 needs to be in one function
        because 'yield's don't bubble up.
        """
        remainder_buf = None
        for num, fobj in enumerate(self.mapped_file_objs):
            df, dummy_name = fobj
            fileobj = df.file_object
            self._check("aw")
            tarinfo = self.tarinfos[num]
            buf = self.tarinfo_bufs[num]
            stream_buffers, remainder_buf = self.prepare_output(buf, remainder_buf)
            for stream_buf in stream_buffers:
                yield stream_buf
            self.offset += len(buf or "")
            if tarinfo.isreg():
                if tarinfo.size == 0:
                    continue
                # split into file read buffer sized chunks
                blocks, remainder = divmod(tarinfo.size, self.buffersize)
                for dummy_b in range(blocks):
                    buf = fileobj.read(self.buffersize)
                    if len(buf) < self.buffersize:
                        raise IOError("end of file reached")
                    # send in http_buffersize sized chunks
                    stream_buffers, remainder_buf = self.prepare_output(
                        buf, remainder_buf
                    )
                    for stream_buf in stream_buffers:
                        yield stream_buf
                # in case the file has remaining read bytes
                if remainder != 0:
                    buf = fileobj.read(remainder)
                    if len(buf) < remainder:
                        raise IOError("end of file reached")
                    # send remaining file data
                    stream_buffers, remainder_buf = self.prepare_output(
                        buf, remainder_buf
                    )
                    for stream_buf in stream_buffers:
                        yield stream_buf
                blocks, remainder = divmod(tarinfo.size, tarfile.BLOCKSIZE)
                if remainder > 0:
                    buf = tarfile.NUL * (tarfile.BLOCKSIZE - remainder)
                    stream_buffers, remainder_buf = self.prepare_output(
                        buf, remainder_buf
                    )
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
            stream_buffers, remainder_buf = self.prepare_output(buf, remainder_buf)
            for stream_buf in stream_buffers:
                yield stream_buf
        if remainder_buf:
            yield remainder_buf
        if self.do_gzip:
            yield self.close_gzip()

    def get_response(self, tracker_data=None):
        if self.do_gzip:
            content_type = "application/x-gzip"
            content_length = None
            self.filename += ".gz"
        else:
            content_type = "application/x-tar"
            content_length = self.tar_size
        file_iterator = IteratorTracker(self.make_tar(), tracker_data)
        response = StreamingHttpResponse(file_iterator, content_type=content_type)
        response["Content-Disposition"] = 'attachment; filename="%s"' % self.filename
        response["X-Accel-Buffering"] = "no"
        if content_length is not None:
            response["Content-Length"] = content_length
        return response


def _streaming_downloader(
    request,
    datafiles,
    rootdir,
    filename,
    comptype="tgz",
    organization=DEFAULT_ORGANIZATION,
):
    """
    private function to be called by wrappers
    creates download response with given files and names
    """
    mapper = make_mapper(organization, rootdir)
    if not mapper:
        return render_error_message(
            request,
            f"Unknown download organization: {organization}",
            status=400,
        )

    if getattr(settings, "ENABLE_EVENTLOG", False):
        from tardis.apps.eventlog.utils import log

        for df in datafiles:
            log(
                action="DOWNLOAD_DATAFILE",
                extra={"id": df.id, "type": "tar"},
                request=request,
            )

    try:
        files = _get_datafile_details_for_archive(mapper, datafiles)
        tfs = UncachedTarStream(files, filename=filename, do_gzip=comptype != "tar")
        tracker_data = {
            "label": "tar",
            "session_id": request.COOKIES.get("_ga"),
            "ip": request.META.get("REMOTE_ADDR", ""),
            "user": request.user,
            "total_size": tfs.tar_size,
            "num_files": len(datafiles),
            "ua": request.META.get("HTTP_USER_AGENT", None),
        }
        return tfs.get_response(tracker_data)
    except ValueError:  # raised when replica not verified TODO: custom excptn
        message = """The experiment you are trying to access has not yet been
                     verified completely.
                     Verification is an automated background process.
                     Please try again later or contact the system
                     administrator if the issue persists."""
        message = " ".join(message.split())  # removes spaces
        return redirect_back_with_error(request, message)


@experiment_download_required
def streaming_download_experiment(
    request, experiment_id, comptype="tgz", organization=DEFAULT_ORGANIZATION
):
    experiment = Experiment.objects.get(id=experiment_id)
    rootdir = get_filesystem_safe_experiment_name(experiment)
    filename = "%s-complete.tar" % rootdir

    df_ids = (
        DataFileObject.objects.filter(
            datafile__dataset__experiments__id=experiment_id, verified=True
        )
        .values("datafile_id")
        .distinct()
    )
    datafiles = DataFile.objects.filter(id__in=df_ids)
    if not settings.ONLY_EXPERIMENT_ACLS:
        # Generator to produce datafile from datafile id
        def get_datafile(datafile):
            if has_download_access(
                request=request, obj_id=datafile.id, ct_type="datafile"
            ):
                yield datafile

        # Take chained generators and turn them into a set of datafiles
        datafiles = set(chain(chain.from_iterable(map(get_datafile, datafiles))))
    if not datafiles:
        message = """The experiment you are trying to access does not contain
                     any DataFiles that you are allowed to download."""
        message = " ".join(message.split())  # removes spaces
        return redirect_back_with_error(request, message)

    return _streaming_downloader(
        request, datafiles, rootdir, filename, comptype, organization
    )


@dataset_download_required
def streaming_download_dataset(
    request, dataset_id, comptype="tgz", organization=DEFAULT_ORGANIZATION
):
    dataset = Dataset.objects.get(id=dataset_id)
    rootdir = get_filesystem_safe_dataset_name(dataset)
    filename = "%s-complete.tar" % rootdir

    df_ids = (
        DataFileObject.objects.filter(datafile__dataset=dataset, verified=True)
        .values("datafile_id")
        .distinct()
    )
    datafiles = DataFile.objects.filter(id__in=df_ids)
    if not settings.ONLY_EXPERIMENT_ACLS:
        # Generator to produce datafile from datafile id
        def get_datafile(datafile):
            if has_download_access(
                request=request, obj_id=datafile.id, ct_type="datafile"
            ):
                yield datafile

        # Take chained generators and turn them into a set of datafiles
        datafiles = set(chain(chain.from_iterable(map(get_datafile, datafiles))))
    if not datafiles:
        message = """The experiment you are trying to access does not contain
                     any DataFiles that you are allowed to download."""
        message = " ".join(message.split())  # removes spaces
        return redirect_back_with_error(request, message)

    return _streaming_downloader(
        request, datafiles, rootdir, filename, comptype, organization
    )


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
    comptype = getattr(settings, "DEFAULT_ARCHIVE_FORMATS", ["tar"])[0]
    organization = getattr(settings, "DEFAULT_PATH_MAPPER", "classic")
    if "comptype" in request.POST:
        comptype = request.POST["comptype"]
    if "organization" in request.POST:
        organization = request.POST["organization"]

    if "datafile" in request.POST or "dataset" in request.POST:
        if request.POST.getlist("datafile") or request.POST.getlist("dataset"):
            datasets = request.POST.getlist("dataset")
            datafiles = request.POST.getlist("datafile")

            # Generator to produce datafiles from dataset id
            def get_dataset_datafiles(dsid):
                for datafile in DataFile.objects.filter(dataset=dsid):
                    if has_download_access(
                        request=request, obj_id=datafile.id, ct_type="datafile"
                    ):
                        yield datafile

            # Generator to produce datafile from datafile id
            def get_datafile(dfid):
                datafile = DataFile.objects.get(pk=dfid)
                if has_download_access(
                    request=request, obj_id=datafile.id, ct_type="datafile"
                ):
                    yield datafile

            # Take chained generators and turn them into a set of datafiles
            df_set = set(
                chain(
                    chain.from_iterable(map(get_dataset_datafiles, datasets)),
                    chain.from_iterable(map(get_datafile, datafiles)),
                )
            )
        else:
            return render_error_message(
                request, "No datasets or files were selected for download", status=404
            )

    elif "url" in request.POST:
        if not request.POST.getlist("url"):
            return render_error_message(
                request,
                "No Datasets or Datafiles were selected for downloaded",
                status=404,
            )

        for url in request.POST.getlist("url"):
            url = urllib.unquote(url)
            raw_path = url.partition("//")[2]
            experiment_id = request.POST["expid"]
            datafile = DataFile.objects.filter(
                url__endswith=raw_path, dataset__experiment__id=experiment_id
            )[0]
            if has_download_access(
                request=request, obj_id=datafile.id, ct_type="datafile"
            ):
                df_set = {datafile}
    else:
        message = "No datasets or datafiles were selected for download"
        return redirect_back_with_error(request, message)

    logger.info(f"Files for archive command: {df_set}")

    if not df_set:
        message = (
            "No verified files were accessible to download in the "
            "selected dataset(s)"
        )
        return redirect_back_with_error(request, message)

    try:
        expid = request.POST["expid"]
        experiment = Experiment.objects.get(id=expid)
    except (KeyError, Experiment.DoesNotExist):
        experiment = next(iter(df_set)).dataset.get_first_experiment()

    exp_title = get_filesystem_safe_experiment_name(experiment)
    filename = f"{exp_title}-selection.tar"
    rootdir = f"{exp_title}-selection"
    return _streaming_downloader(
        request, df_set, rootdir, filename, comptype, organization
    )


@login_required
def download_api_key(request):
    user = request.user
    api_key_file = io.StringIO()
    api_key_file.write("ApiKey {0}:{1}".format(user, user.api_key.key))
    api_key_file.seek(0)
    response = StreamingHttpResponse(
        FileWrapper(api_key_file), content_type="text/plain"
    )
    response["Content-Disposition"] = 'attachment; filename="{0}.key"'.format(user)
    return response
