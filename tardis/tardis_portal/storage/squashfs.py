'''
SquashFS Storage Box


setup requirements:
user-owned mount root dir
mytardis user must have access to files in squashfs file based on immutable
permissions set in squashfile. In easy cases, one group owns everything and the
mytardis user can be added to that group.

set up autofs to auto-mount squashfiles
'''

import logging
import os

from celery.task import task

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.utils.importlib import import_module

from tardis.tardis_portal.models import DataFile, DatafileParameterSet, \
    StorageBoxOption

log = logging.getLogger(__name__)


class SquashFSStorage(FileSystemStorage):
    """
    Only works for autofs mounted squashfs files
    Please provide a setting that maps source dir and mount dir, e.g.:
    SQUASHFS_DIRS = {'tape': {'source': '/my/tape/mount',
                              'autofs': '/taped-squashfiles'},
                     'volume': {'source': '/my/volume/storage',
                                'autofs': '/volumed-squashfiles'}}
    """
    squashfs_dirs = getattr(settings, 'SQUASHFS_DIRS')

    def __init__(self, sq_filename=None, datafile_id=None, sq_dir=None):
        if SquashFSStorage.squashfs_dirs is None:
            raise ImproperlyConfigured('Please configure SQUASHFS_DIRS')
        autofs_dir, name = None, None
        if sq_filename is not None and sq_dir is not None:
            name, ext = os.path.splitext(sq_filename)
            autofs_dir = SquashFSStorage.squashfs_dirs[sq_dir]['autofs']
        elif datafile_id is not None:
            df = DataFile.objects.get(id=datafile_id)
            name, ext = os.path.splitext(df.filename)
            if sq_dir is None:
                # guess location
                dfo = df.get_preferred_dfo()
                try:
                    base_dir = dfo.storage_box.options.get(key='location')
                except StorageBoxOption.DoesNotExist:
                    raise ImproperlyConfigured('SquashFS files have '
                                               'misconfigured locations')
                for key, val in SquashFSStorage.squashfs_dirs.iteritems():
                    if base_dir == val['source']:
                        autofs_dir = val['autofs']
                        break
            else:
                autofs_dir = SquashFSStorage.squashfs_dirs[sq_dir]['autofs']
        if autofs_dir is None or name is None:
            raise Exception('provide squash file name or datafile id '
                            'and location')
        location = os.path.join(autofs_dir, name)
        super(SquashFSStorage, self).__init__(location=location)

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
