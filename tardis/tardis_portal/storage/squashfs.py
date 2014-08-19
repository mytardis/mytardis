'''
SquashFS Storage Box
'''
import errno
import os
import subprocess

from datetime import datetime

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.core.files.storage import Storage
from django.utils._os import safe_join

'''
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


class SquashFSStorage(Storage):
    """
    The default mounter is squashfuse, which can be found here:
    https://github.com/vasi/squashfuse

    setting:
    SQUASHFS_MOUNT_ROOT = '/mnt/squashfs'
    SQUASHFS_MOUNT_CMD = "/usr/local/bin/squashfuse"
    """

    squashmount_root = getattr(settings,
                               'SQUASHFS_MOUNT_ROOT',
                               '/mnt/squashfs')

    def __init__(self, sq_filename=None, sq_basepath=None):
        if sq_filename is None or sq_basepath is None:
            raise Exception('provide squash file name and path')
        self.sq_filename = sq_filename
        self.location = os.path.join(self.squashmount_root,
                                     sq_filename)
        self.squashfile = os.path.join(sq_basepath, sq_filename)
        self._mount()

    @property
    def _mounted(self):
        mount_list = subprocess.check_output(['mount'], shell=False)
        return mount_list.find(self.location) > -1

    def _mount(self):
        if self._mounted:
            return
        squashmount_cmd = getattr(settings,
                                  'SQUASHFSMOUNT_CMD',
                                  '/usr/local/bin/squashfuse')
        try:
            os.makedirs(self.location)
        except OSError as exc:
            if not (exc.errno == errno.EEXIST and
                    os.path.isdir(self.location)):
                raise
        subprocess.call([squashmount_cmd,
                         self.squashfile, self.location])

    def _open(self, name, mode='rb'):
        '''
        tries mounting squashfs file once,
        then raises whichever error is raised by open(filename)
        '''
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
        split_path = os.path.split(dfo.uri)
        if split_path[0] == sq_name:
            return os.path.join(split_path[1:])
        else:
            return dfo.uri
