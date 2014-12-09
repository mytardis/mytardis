'''
SquashFS Storage Box


setup requirements:
user-owned mount root dir
user added to fuse group

building squashfuse:
apt-get install autoconf libfuse-dev liblzma-dev liblzo2-dev liblz4-dev
git clone https://github.com/vasi/squashfuse.git
cd squashfuse
./autogen.sh
./configure
make
sudo make install
'''
import errno
import os
import subprocess

from celery import task
from datetime import datetime
from magic import Magic

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.core.files.storage import Storage
from django.db.models import Q
from django.utils._os import safe_join
from django.utils.importlib import import_module

from tardis.tardis_portal.models import (
    Dataset, DataFile, DataFileObject,
    DatafileParameterSet
)
from tardis.tardis_portal.util import generate_file_checksums

import logging
log = logging.getLogger(__name__)


class SquashFSStorage(Storage):
    """
    The default mounter is squashfuse, which can be found here:
    https://github.com/vasi/squashfuse

    settings:
    SQUASHFS_MOUNT_ROOT = '/mnt/squashfs'
    SQUASHFS_MOUNT_CMD = "/usr/local/bin/squashfuse"

    datafile_id only works for block storage
    """

    squashmount_root = getattr(settings,
                               'SQUASHFS_MOUNT_ROOT',
                               '/mnt/squashfs')
    squashmount_cmd = getattr(settings,
                              'SQUASHFSMOUNT_CMD',
                              '/usr/local/bin/squashfuse')

    def __init__(self, sq_filename=None, sq_basepath=None, datafile_id=None):
        if sq_filename is not None and sq_basepath is not None:
            self.sq_filename = sq_filename
            self.location = os.path.join(self.squashmount_root,
                                         sq_filename)
            self.squashfile = os.path.join(sq_basepath, sq_filename)
            self._mount()
        elif datafile_id is not None:
            df = DataFile.objects.get(id=datafile_id)
            self.location = os.path.join(self.squashmount_root, df.filename)
            self.squashfile = df.default_dfo.get_full_path()
            self._mount()
        else:
            raise Exception('provide squash file name and path or datafile id')

    def __del__(self):
        self._umount()

    @property
    def _mounted(self):
        mount_list = subprocess.check_output(['mount'], shell=False)
        return mount_list.find(self.location) > -1

    def _mount(self):
        if self._mounted:
            return
        try:
            os.makedirs(self.location)
        except OSError as exc:
            if not (exc.errno == errno.EEXIST and
                    os.path.isdir(self.location)):
                raise
        subprocess.call([self.squashmount_cmd,
                         self.squashfile, self.location])
        return self._mounted

    def _umount(self):
        if self._mounted:
            subprocess.call(['fusermount', '-u', self.location])
        return self._mounted

    def _open(self, name, mode='rb'):
        '''
        tries mounting squashfs file once,
        then raises whichever error is raised by open(filename)
        '''
        self._mount()
        return File(open(self.path(name), mode))

    def exists(self, name):
        return os.path.exists(self.path(name))

    def listdir(self, path):
        path = self.path(path)
        directories, files = [], []
        for entry in os.listdir(path):
            if os.path.isdir(os.path.join(path, entry)):
                directories.append(entry)
            else:
                files.append(entry)
        return directories, files

    def path(self, name):
        try:
            path = safe_join(self.location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)
        return os.path.normpath(path)

    def size(self, name):
        return os.path.getsize(self.path(name))

    def accessed_time(self, name):
        return datetime.fromtimestamp(os.path.getatime(self.path(name)))

    def created_time(self, name):
        return datetime.fromtimestamp(os.path.getctime(self.path(name)))

    def modified_time(self, name):
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)))

    def build_identifier(self, dfo):
        if dfo.uri is None:
            return None
        sq_name = self.sq_filename.replace('.squashfs', '')
        split_path = dfo.uri.split(os.sep)
        if split_path[0] == sq_name:
            return os.path.join(split_path[1:])
        else:
            return dfo.uri

    def walk(self, top='.', topdown=True, onerror=None, ignore_dotfiles=True):
        try:
            dirnames, filenames = self.listdir(top)
        except os.error as err:
            if onerror is not None:
                onerror(err)
            return
        if ignore_dotfiles:
            dirnames = [d for d in dirnames if not d.startswith('.')]
            filenames = [f for f in filenames if not f.startswith('.')]
        if topdown:
            yield top, dirnames, filenames
        for dirname in dirnames:
            new_top = os.path.join(top, dirname)
            for result in self.walk(new_top):
                yield result
        if not topdown:
            yield top, dirnames, filenames


@task
def parse_new_squashfiles():
    '''
    settings variable SQUASH_PARSERS contains a dictionary of Datafile schemas
    and Python module load strings.

    The Python module loaded must contain a function 'parse_squash_file',
    which will do the work.
    '''
    parsers = getattr(settings, 'SQUASHFS_PARSERS', {})
    for ns, parse_module in parsers.iteritems():
        unparsed_files = DatafileParameterSet.objects.filter(
            schema__namespace=ns,
            datafileparameter__name__name='parse_status'
        ).exclude(
            datafileparameter__string_value='complete'
        ).exclude(
            datafileparameter__string_value='running'
        ).values_list('datafile_id', flat=True)

        for sq_file_id in unparsed_files:
            parse_squashfs_file.delay(sq_file_id, parse_module, ns)


def get_parse_status(squash_datafile, ns):
    from tardis.tardis_portal.models import DatafileParameter
    try:
        status = squash_datafile.datafileparameterset_set.get(
            schema__namespace=ns
        ).datafileparameter_set.get(
            name__name='parse_status')
    except DatafileParameter.DoesNotExist:
        from tardis.tardis_portal.models import (Schema, ParameterName)
        schema = Schema.objects.get(type=Schema.DATAFILE,
                                    namespace=ns)
        pn, created = ParameterName.objects.get_or_create(
            name='parse_status',
            schema=schema,
            data_type=ParameterName.STRING)
        ps = squash_datafile.datafileparameterset_set.get(schema=schema)
        status = DatafileParameter(parameterset=ps,
                                   name=pn,
                                   string_value='new')
        status.save()
    return status


@task
def parse_squashfs_file(squashfs_file_id, parse_module, ns):
    '''
    the status check doesn't provide complete protection against duplicate
    parsing, but should be fine when the interval between runs
    '''
    squashfile = DataFile.objects.get(id=squashfs_file_id)
    status = get_parse_status(squashfile, ns)
    if status.string_value in ['complete', 'running']:
        return
    status.string_value = 'running'
    status.save()
    parser = import_module(parse_module)

    try:
        parser.parse_squashfs_file(squashfile, ns)
        status.string_value = 'complete'
    except:
        status.string_value = 'parse failed'
        raise
    finally:
        status.save()
