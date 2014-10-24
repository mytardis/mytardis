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

from datetime import datetime
from magic import Magic

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.core.files.storage import Storage
from django.db.models import Q
from django.utils._os import safe_join
from django.utils.importlib import import_module

from tardis.tardis_portal.models import Dataset, DataFile, DataFileObject
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
    """

    squashmount_root = getattr(settings,
                               'SQUASHFS_MOUNT_ROOT',
                               '/mnt/squashfs')
    squashmount_cmd = getattr(settings,
                              'SQUASHFSMOUNT_CMD',
                              '/usr/local/bin/squashfuse')

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
        try:
            os.makedirs(self.location)
        except OSError as exc:
            if not (exc.errno == errno.EEXIST and
                    os.path.isdir(self.location)):
                raise
        subprocess.call([self.squashmount_cmd,
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
        split_path = dfo.uri.split(os.sep)
        if split_path[0] == sq_name:
            return os.path.join(split_path[1:])
        else:
            return dfo.uri


def dj_storage_walk(dj_storage, top='.', topdown=True, onerror=None,
                    ignore_dotfiles=True):
    try:
        dirnames, filenames = dj_storage.listdir(top)
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
        for result in dj_storage_walk(dj_storage, new_top):
            yield result
    if not topdown:
        yield top, dirnames, filenames


def get_parser_module(exp):
    parsers = getattr(settings, 'SQUASH_PARSERS', {})
    namespaces = exp.experimentparameterset_set.all().values_list(
        'schema__namespace', flat=True)
    for ns in namespaces:
        parser = parsers.get(ns)
        if parser is not None:
            return import_module(parser)
    return None


def squash_parse_box_data(exp, squash_sbox, inst):
    parser_module = get_parser_module(exp)
    if parser_module is not None:
        return parser_module.parse_squashfs_box_data(exp, squash_sbox, inst)


def squash_parse_datafile(exp, squash_sbox, inst,
                          directory, filename, filepath, box_data):
    '''
    return matching or new datafile for given squashfs file path.

    parse discipline specific if set up

    by default use 'squashfs-files' as dataset name
    '''
    parser_module = get_parser_module(exp)
    if parser_module is not None:
        return parser_module.parse_squashfs_file(exp, squash_sbox,
                                                 inst, directory,
                                                 filename, filepath, box_data)

    exp_q = Q(datafile__dataset__experiments=exp)
    path_part_match_q = Q(uri__endswith=filepath)
    path_exact_match_q = Q(uri=filepath)
    s_box_q = Q(storage_box=squash_sbox)
    # check whether file has been registered alread, stored elsewhere:
    dfos = DataFileObject.objects.filter(exp_q, path_part_match_q,
                                         ~s_box_q)
    if len(dfos) == 1:
        return dfos[0].datafile
    # file registered already
    dfos = DataFileObject.objects.filter(exp_q, path_exact_match_q, s_box_q)
    if len(dfos) == 1:
        return dfos[0]

    default_name = 'squashfs-files'
    datasets = Dataset.objects.filter(experiments=exp,
                                      description=default_name,
                                      storage_boxes=squash_sbox)
    if datasets.count() >= 1:
        dataset = datasets[0]
    else:
        dataset = Dataset(description=default_name)
        dataset.save()
        dataset.experiments.add(exp)
        dataset.storage_boxes.add(squash_sbox)

    filesize = inst.size(filepath)
    md5, sha512, size, mimetype_buffer = generate_file_checksums(
        inst.open(filepath))
    mimetype = ''
    if len(mimetype_buffer) > 0:
        mimetype = Magic(mime=True).from_buffer(mimetype_buffer)
    df_dict = {'dataset': dataset,
               'filename': filename,
               'directory': directory,
               'size': filesize,
               'created_time': inst.created_time(filepath),
               'modification_time': inst.modified_time(filepath),
               'mimetype': mimetype,
               'md5sum': md5,
               'sha512sum': sha512}
    df = DataFile(**df_dict)
    df.save()
    return df


def squashfs_match_experiment(exp, squash_sbox, ignore_dotfiles=True):
    '''matches files already existing in experiment to a squashfs file
    registered as storage box.  '''

    inst = squash_sbox.get_initialised_storage_instance()
    box_data = squash_parse_box_data(exp, squash_sbox, inst)
    for basedir, dirs, files in dj_storage_walk(inst):
        for filename in files:
            filepath = os.path.join(basedir, filename)
            parse_result = squash_parse_datafile(exp, squash_sbox, inst,
                                                 basedir, filename, filepath,
                                                 box_data)
            if type(parse_result) == DataFile:
                new_dfo = DataFileObject(datafile=parse_result,
                                         storage_box=squash_sbox,
                                         uri=filepath)
                new_dfo.save()
