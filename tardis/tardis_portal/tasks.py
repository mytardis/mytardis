from celery.task import task
from os import path
from django.db import transaction
from django.contrib.auth.models import User

from tardis.tardis_portal.staging import stage_file
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
    for datafile in Dataset_File.objects.filter(verified=False):
        if datafile.stay_remote or datafile.is_local():
            verify_as_remote.delay(datafile.id)
        else:
            make_local_copy.delay(datafile.id)

@task(name="tardis_portal.verify_as_remote", ignore_result=True)
def verify_as_remote(datafile_id):
    datafile = Dataset_File.objects.get(id=datafile_id)
    # Check that we still need to verify - it might have been done already
    if datafile.verified:
        return
    # Use a transaction for safety
    with transaction.commit_on_success():
        # Get datafile locked for write (to prevent concurrent actions)
        datafile = Dataset_File.objects.select_for_update().get(id=datafile.id)
        # Second check after lock (concurrency paranoia)
        if not datafile.verified:
            datafile.verify()

@task(name="tardis_portal.make_local_copy", ignore_result=True)
def make_local_copy(datafile_id):
    datafile = Dataset_File.objects.get(id=datafile_id)
    # Check that we still need to verify - it might have been done already
    if datafile.is_local():
        return
    # Use a transaction for safety
    with transaction.commit_on_success():
        # Get datafile locked for write (to prevent concurrent actions)
        datafile = Dataset_File.objects.select_for_update().get(id=datafile_id)
        # Second check after lock (concurrency paranoia)
        if not datafile.is_local():
            stage_file(datafile)

@task(name="tardis_portal.create_staging_datafiles", ignore_result=True)
def create_staging_datafiles(files, user_id, dataset_id):
    import os
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

    current_site = Site.objects.get_current()

    context = Context({
        'username': user.username,
        'current_site': current_site.domain,
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
                            protocol='staging',
                            url=url,
                            filename=path.basename(filepath),
                            size=size)
    datafile.verify(allowEmptyChecksums=True)
    datafile.save()
    

@task(name="tardis_portal.email_user_task", ignore_result=True)
def email_user_task(subject, template_name, context, user):
    email_user(subject, template_name, context, user)