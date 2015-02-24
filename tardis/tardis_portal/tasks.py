
import os
from os import path

from celery import group, chain
from celery.task import task

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import transaction
from django.template import Context

from tardis.tardis_portal.models import DataFile
from tardis.tardis_portal.models import DataFileObject
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.staging import get_staging_url_and_size
from tardis.tardis_portal.email import email_user

# Ensure filters are loaded
try:
    from tardis.tardis_portal.filters import FilterInitMiddleware
    FilterInitMiddleware()
except Exception:
    pass

# For ApiKey hooks:
import tardis.tardis_portal.models.hooks

try:
    from tardis.tardis_portal.logging_middleware import LoggingMiddleware
    LoggingMiddleware()
except Exception:
    pass


@task(name="tardis_portal.verify_dfos", ignore_result=True)
def verify_dfos(dfos=None):
    dfos_to_verify = dfos or DataFileObject.objects\
                                           .filter(verified=False)
    for dfo in dfos_to_verify:
        verify_dfo.delay(dfo.id)


@task(name="tardis_portal.verify_dfo", ignore_result=True)
def verify_dfo(dfo_id, only_local=False, reverify=False):
    '''
    verify task
    allowemtpychecksums is false for auto-verify, hence the parameter
    '''
    # Use a transaction for safety
    with transaction.commit_on_success():
        # Get dfo locked for write (to prevent concurrent actions)
        dfo = DataFileObject.objects.select_for_update().get(id=dfo_id)
        if reverify or not dfo.verified:
            dfo.verify()


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


# this should really be defined in the app, need to check if celery picks
# up tasks in apps
try:
    from tardis.apps.publication_forms.tasks import update_publication_records

    @task(name="tardis_portal.update_publication_records", ignore_result=True)
    def update_publication_records_task():
        update_publication_records()
except ImportError:
    pass
