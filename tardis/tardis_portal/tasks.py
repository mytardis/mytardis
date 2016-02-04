# pylint: disable=R0204
import os
from os import path

from celery import group, chain
from celery.task import task

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import transaction
from django.db.models import Q
from django.template import Context

from tardis.tardis_portal.staging import get_staging_url_and_size
from tardis.tardis_portal.email import email_user


# Ensure filters are loaded
try:
    from tardis.tardis_portal.filters import FilterInitMiddleware
    FilterInitMiddleware()
except Exception:
    pass
try:
    from tardis.tardis_portal.logging_middleware import LoggingMiddleware
    LoggingMiddleware()
except Exception:
    pass


@task(name="tardis_portal.verify_dfos", ignore_result=True)
def verify_dfos(dfos=None, **kwargs):
    from tardis.tardis_portal.models import DataFileObject
    dfos_to_verify = dfos or DataFileObject.objects\
                                           .filter(verified=False)
    kwargs['transaction_lock'] = kwargs.get('transaction_lock', True)
    for dfo in dfos_to_verify:
        dfo_verify.apply_async(args=[dfo.id], **kwargs)


@task(name='tardis_portal.ingest_received_files', ignore_result=True)
def ingest_received_files():
    '''
    finds all files stored in temporary storage boxes and attempts to move
    them to their permanent home
    '''
    from tardis.tardis_portal.models import StorageBox
    ingest_boxes = StorageBox.objects.filter(Q(attributes__key='type'),
                                             Q(attributes__value='receiving'),
                                             ~Q(master_box=None))
    for box in ingest_boxes:
        box.move_to_master.delay()


@task(name="tardis_portal.create_staging_datafiles", ignore_result=True)  # too complex # noqa
def create_staging_datafiles(files, user_id, dataset_id, is_secure):

    from tardis.tardis_portal.staging import get_full_staging_path

    def f7(seq):
        # removes any duplicate files that resulted from traversal
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]

    def list_dir(dir):
        # returns a list from a recursive directory search
        file_list = []

        for dirname, dirnames, filenames in os.walk(dir):
            for filename in filenames:
                file_list.append(os.path.join(dirname, filename))

        return file_list

    user = User.objects.get(id=user_id)
    staging = get_full_staging_path(user.username)
    stage_files = []

    for f in files:
        abs_path = ''
        if f == 'phtml_1':
            abs_path = staging
        else:
            abs_path = path.join(staging, f)

        if path.isdir(abs_path):
            stage_files = stage_files + list_dir(abs_path)
        else:
            stage_files.append(abs_path)

    full_file_list = f7(stage_files)

    protocol = ""
    if is_secure:
        protocol = "s"
    current_site_complete = "http%s://%s" % (protocol,
                                             Site.objects.get_current().domain)

    context = Context({
        'username': user.username,
        'current_site': current_site_complete,
        'dataset_id': dataset_id,
    })
    subject = '[MyTardis] Import Successful'

    # traverse directory paths (if any to build file list)
    job = group(
        create_staging_datafile.s(f, user.username, dataset_id)
        for f in full_file_list)
    if user.email:
        job = chain(job,
                    email_user_task.s(
                        subject, 'import_staging_success', context, user))
    job().delay()


@task(name="tardis_portal.create_staging_datafile", ignore_result=True)
def create_staging_datafile(filepath, username, dataset_id):
    from tardis.tardis_portal.models import DataFile, Dataset
    dataset = Dataset.objects.get(id=dataset_id)

    url, size = get_staging_url_and_size(username, filepath)
    datafile = DataFile(dataset=dataset,
                        filename=path.basename(filepath),
                        size=size)
    datafile.save()
    datafile.file_object = open(filepath, 'r')


@task(name="tardis_portal.email_user_task", ignore_result=True)
def email_user_task(subject, template_name, context, user):
    email_user(subject, template_name, context, user)


@task(name='tardis_portal.cache_notify', ignore_result=True)
def cache_done_notify(results, user_id, site_id, ct_id, obj_ids):
    user = User.objects.get(id=user_id)
    site = Site.objects.get(id=site_id)
    subject = '[{site}] Cache recall done'.format(site=site.name)
    ct = ContentType.objects.get(id=ct_id)
    objects = [ct.get_object_for_this_type(id=obj_id) for obj_id in obj_ids]
    context = {
        'objects': objects,
        'username': user.username,
    }
    email_user(subject, 'cache_done_email', context, user)
    return "all done"


# "method tasks"
# StorageBox
@task(name="tardis_portal.storage_box.copy_files", ignore_result=True)
def sbox_copy_files(sbox_id, dest_box_id=None, *args, **kwargs):
    from tardis.tardis_portal.models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return sbox.copy_files(dest_box=dest_box, *args, **kwargs)


@task(name="tardis_portal.storage_box.move_files", ignore_result=True)
def sbox_move_files(sbox_id, dest_box_id=None, *args, **kwargs):
    from tardis.tardis_portal.models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return sbox.move_files(dest_box=dest_box, *args, **kwargs)


@task(name='tardis_portal.storage_box.copy_to_master')
def sbox_copy_to_master(sbox_id, *args, **kwargs):
    from tardis.tardis_portal.models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    return sbox.copy_to_master(*args, **kwargs)


@task(name='tardis_portal.storage_box.move_to_master')
def sbox_move_to_master(sbox_id, *args, **kwargs):
    from tardis.tardis_portal.models import StorageBox
    sbox = StorageBox.objects.get(id=sbox_id)
    return sbox.move_to_master(*args, **kwargs)


# DataFile
@task(name="tardis_portal.cache_datafile", ignore_result=True)
def df_cache_file(df_id):
    from tardis.tardis_portal.models import DataFile
    df = DataFile.objects.get(id=df_id)
    return df.cache_file()


# DataFileObject
@task(name='tardis_portal.dfo.move_file', ignore_result=True)
def dfo_move_file(dfo_id, dest_box_id=None):
    from tardis.tardis_portal.models import DataFileObject, StorageBox
    dfo = DataFileObject.objects.get(id=dfo_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return dfo.move_file(dest_box)


@task(name='tardis_portal.dfo.copy_file', ignore_result=True)
def dfo_copy_file(dfo_id, dest_box_id=None, *args, **kwargs):
    from tardis.tardis_portal.models import DataFileObject, StorageBox
    dfo = DataFileObject.objects.get(id=dfo_id)
    if dest_box_id is not None:
        dest_box = StorageBox.objects.get(id=dest_box_id)
    else:
        dest_box = None
    return dfo.copy_file(dest_box=dest_box, *args, **kwargs)


@task(name='tardis_portal.dfo.cache_file', ignore_result=True)
def dfo_cache_file(dfo_id):
    from tardis.tardis_portal.models import DataFileObject
    dfo = DataFileObject.objects.get(id=dfo_id)
    return dfo.cache_file()


@task(name="tardis_portal.dfo.verify", ignore_result=True)
def dfo_verify(dfo_id, *args, **kwargs):
    from tardis.tardis_portal.models import DataFileObject
    # Get dfo locked for write (to prevent concurrent actions)
    if kwargs.pop('transaction_lock', False):
        with transaction.atomic():
            dfo = DataFileObject.objects.select_for_update().get(id=dfo_id)
            return dfo.verify(*args, **kwargs)
    dfo = DataFileObject.objects.get(id=dfo_id)
    dfo.verify(*args, **kwargs)
