from celery.task import task
import os
from os import path
from django.db import transaction
from django.contrib.auth.models import User

from tardis.tardis_portal.staging import stage_replica
from tardis.tardis_portal.models import Replica
from tardis.tardis_portal.models import Location
from tardis.tardis_portal.models import Dataset_File, Dataset
from tardis.tardis_portal.staging import get_staging_url_and_size
from tardis.tardis_portal.email import email_user

from django.template import Context

from django.contrib.sites.models import Site

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

@task(name="tardis_portal.verify_files", ignore_result=True)
def verify_files():
    for replica in Replica.objects.filter(verified=False):
        if replica.stay_remote or replica.is_local():
            verify_as_remote.delay(replica.id)
        else:
            make_local_copy.delay(replica.id)

@task(name="tardis_portal.verify_as_remote", ignore_result=True)
def verify_as_remote(replica_id):
    replica = Replica.objects.get(id=replica_id)
    # Check that we still need to verify - it might have been done already
    if replica.verified:
        return
    # Use a transaction for safety
    with transaction.commit_on_success():
        # Get replica locked for write (to prevent concurrent actions)
        replica = Replica.objects.select_for_update().get(id=replica.id)
        # Second check after lock (concurrency paranoia)
        if not replica.verified:
            replica.verify()
            replica.save()

@task(name="tardis_portal.make_local_copy", ignore_result=True)
def make_local_copy(replica_id):
    replica = Replica.objects.get(id=replica_id)
    # Check that we still need to verify - it might have been done already
    if replica.is_local():
        return
    # Use a transaction for safety
    with transaction.commit_on_success():
        # Get replica locked for write (to prevent concurrent actions)
        replica = Replica.objects.select_for_update().get(id=replica_id)
        # Second check after lock (concurrency paranoia)
        if not replica.is_local():
            stage_replica(replica)


@task(name="tardis_portal.create_staging_datafiles", ignore_result=True)
def create_staging_datafiles(files, user_id, dataset_id, is_secure):

    from os import path

    from tardis.tardis_portal.staging import get_full_staging_path

    def f7(seq):
        # removes any duplicate files that resulted from traversal
        seen = set()
        seen_add = seen.add
        return [ x for x in seq if x not in seen and not seen_add(x)]

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

    # traverse directory paths (if any to build file list)

    [create_staging_datafile.delay(f, user.username, dataset_id) for f in full_file_list]

    protocol = ""
    if is_secure:
        protocol = "s"
    current_site_complete = "http%s://%s" % (protocol, Site.objects.get_current().domain)

    context = Context({
        'username': user.username,
        'current_site': current_site_complete,
        'dataset_id': dataset_id,
    })
    subject = '[MyTardis] Import Successful'

    if not user.email:
        return None

    email_user_task.delay(subject, 'import_staging_success', context, user)


@task(name="tardis_portal.create_staging_datafile", ignore_result=True)
def create_staging_datafile(filepath, username, dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)

    url, size = get_staging_url_and_size(username, filepath)
    datafile = Dataset_File(dataset=dataset,
                            filename=path.basename(filepath),
                            size=size)
    replica = Replica(datafile=datafile,
                      protocol='staging',
                      url=url,
                      location=Location.get_location('staging'))
    replica.verify(allowEmptyChecksums=True)
    datafile.save()
    replica.datafile = datafile
    replica.save()


@task(name="tardis_portal.email_user_task", ignore_result=True)
def email_user_task(subject, template_name, context, user):
    email_user(subject, template_name, context, user)
