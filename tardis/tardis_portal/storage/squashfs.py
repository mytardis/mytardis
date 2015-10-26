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
import tempfile

from celery import task
from datetime import datetime

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.core.files.storage import Storage
from django.utils._os import safe_join
from django.utils.importlib import import_module

from tardis.tardis_portal.models import DataFile, DatafileParameterSet

import logging
log = logging.getLogger(__name__)


class SquashFSFile(File):

    def __init__(self, *args, **kwargs):
        self.storage_box_instance = kwargs.pop('storage_box_instance')
        super(SquashFSFile, self).__init__(*args, **kwargs)

    def __del__(self, *args, **kwargs):
        self.close()


class SquashFSStorage(Storage):
    """
    Fuse mounting is not reliable. To use this requires bash scripts, examples
    attached at the end of the file. These scripts need to be allowed for sudo
    execution by the Gunicorn user.
    The paths can be set in settings. They default to /usr/local/bin/...

    settings:
    SQUASHFS_MOUNT_ROOT = '/mnt/squashfs'
    SQUASHFS_MOUNT_CMD = "/usr/local/bin/squashfsmount"
    SQUASHFS_UMOUNT_CMD = "/usr/local/bin/squashfsumount"

    datafile_id only works for block storage
    """

    squashmount_root = getattr(settings,
                               'SQUASHFS_MOUNT_ROOT',
                               '/mnt/squashfs')
    squashmount_cmd = getattr(settings,
                              'SQUASHFSMOUNT_CMD',
                              '/usr/local/bin/squashfsmount')
    squashumount_cmd = getattr(settings,
                               'SQUASHFSUMOUNT_CMD',
                               '/usr/local/bin/squashfsumount')

    def __init__(self, sq_filename=None, sq_basepath=None, datafile_id=None):
        # create unique temporary mount point
        tempfile.tempdir = self.squashmount_root
        self.mount_dir = tempfile.mkdtemp()
        self.mount_dir_name = os.path.basename(self.mount_dir)
        tempfile.tempdir = None

        self.datafile = None
        if sq_filename is not None and sq_basepath is not None:
            self.sq_filename = sq_filename
            self.location = os.path.join(self.mount_dir, sq_filename)
            self.squashfile = os.path.join(sq_basepath, sq_filename)
            self._mount()
        elif datafile_id is not None:
            df = DataFile.objects.get(id=datafile_id)
            self.datafile = df
            self.location = os.path.join(self.mount_dir, df.filename)
            self.squashfile = df.file_objects.all()[0].get_full_path()
            self.sq_filename = os.path.basename(self.squashfile)
            self._mount()
        else:
            raise Exception('provide squash file name and path or datafile id')

    def __del__(self):
        self._umount()
        os.rmdir(self.location)
        os.rmdir(self.mount_dir)

    @property
    def _mounted(self):
        mount_list = subprocess.check_output(['mount'], shell=False)
        return mount_list.find(self.location) > -1

    def _mount(self):
        # example scripts
        # /usr/local/bin/squashfsmount self.squashfile self.mount_dir_name
        """
        #!/usr/bin/python

        import os
        import shlex
        import subprocess
        import sys

        USERNAME = 'mytardis'
        SQUASHPATH = sys.argv[1]
        MOUNT_ID = os.path.basename(sys.argv[2])  # basename for security reasons
        FILENAME = os.path.basename(SQUASHPATH)
        MOUNTDIR = os.path.join('/srv/squashfsmounts', MOUNT_ID, FILENAME)
        if MOUNTDIR in subprocess.check_output('mount'):
            quit()
        subprocess.call(shlex.split('mkdir -p {}'.format(MOUNTDIR)))
        subprocess.call(shlex.split(
            'mount -t squashfs -o ro {squashpath} {mountdir}'.format(
                squashpath=SQUASHPATH, mountdir=MOUNTDIR
        )))
        """
        if not self._mounted:
            subprocess.call(['sudo', self.squashmount_cmd, self.squashfile,
                             self.mount_dir_name])
        return self._mounted

    def _umount(self):
        # /usr/local/bin/squashfsumount self.sq_filename self.mount_dir_name
        """
        #!/usr/bin/python

        import os
        import shlex
        import subprocess
        import sys

        FILENAME = sys.argv[1]
        MOUNT_ID = os.path.basename(sys.argv[2])  # for security reasons
        MOUNTDIR = os.path.join('/srv/squashfsmounts', MOUNT_ID, FILENAME)
        if MOUNTDIR not in subprocess.check_output('mount'):
            quit()
        subprocess.call(shlex.split(
            'umount {mountdir}'.format(mountdir=MOUNTDIR
        )))
        """
        if self._mounted:
            subprocess.call(['sudo', self.squashumount_cmd, self.sq_filename,
                             self.mount_dir_name])
        return self._mounted

    def _open(self, name, mode='rb'):
        '''
        tries mounting squashfs file once,
        then raises whichever error is raised by open(filename)
        '''
        self._mount()
        return SquashFSFile(
            open(self.path(name), mode), storage_box_instance=self)

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


@task(name='tardis_portal.storage.squashfs.parse_new_squashfiles',
      ignore_result=True)
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
            schema__namespace=ns
        ).exclude(
            datafileparameter__name__name='parse_status',
            datafileparameter__string_value='complete'
        ).exclude(
            datafileparameter__name__name='parse_status',
            datafileparameter__string_value='running'
        ).order_by('-id').values_list('datafile_id', flat=True)

        for sq_file_id in unparsed_files:
            parse_squashfs_file.apply_async(
                args=(sq_file_id, parse_module, ns),
                queue='low_priority_queue')


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


@task(name='tardis_portal.storage.squashfs.parse_squashfs_file',
      ignore_result=True)
def parse_squashfs_file(squashfs_file_id, parse_module, ns):
    '''
    the status check doesn't provide complete protection against duplicate
    parsing, but should be fine when the interval between runs is reasonable
    '''
    squashfile = DataFile.objects.get(id=squashfs_file_id)
    status = get_parse_status(squashfile, ns)
    if status.string_value in ['complete', 'running']:
        return
    elif not squashfile.verified:
        status.string_value = 'unverified squashfs file'
        status.save()
        return
    status.string_value = 'running'
    status.save()
    parser = import_module(parse_module)

    try:
        if parser.parse_squashfs_file(squashfile, ns):
            status.string_value = 'complete'
        else:
            status.string_value = 'incomplete'
    except Exception as e:
        log.exception('squash file parse error. id: %s' % squashfs_file_id)
        status.string_value = 'error'
        raise
    finally:
        status.save()
