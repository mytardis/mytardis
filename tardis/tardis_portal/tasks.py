from celery.task import task
from os import path
from django.db import transaction

from tardis.tardis_portal.staging import stage_file
from tardis.tardis_portal.models import Dataset_File, Dataset
from tardis.tardis_portal.staging import get_staging_url_and_size

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
    return datafile