
import os
from os import path
import time

from celery.task import task

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import transaction
from django.template import Context

from tardis.tardis_portal.staging import get_staging_url_and_size
from tardis.tardis_portal.email import email_user

from tardis.tardis_portal.staging import stage_replica

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

# set up redis connection pool. TODO: do this only in celery workers
if getattr(settings, 'REDIS_VERIFY_MANAGER', False):
    import redis  # only import if this installation uses redis
    rvms = getattr(settings, 'REDIS_VERIFY_MANAGER_SETUP',
                   {'host': 'localhost',
                    'port': 6379,
                    'db': 0, })
    redis_verify_manager_pool = redis.ConnectionPool(
        host=rvms['host'], port=rvms['port'], db=rvms['db'])


@task(name="tardis_portal.verify_files", ignore_result=True)
def verify_files(replicas=None):
    from tardis.tardis_portal.models import Replica
    if getattr(settings, 'REDIS_VERIFY_MANAGER', False):
        r = redis.Redis(connection_pool=redis_verify_manager_pool)

    replicas_to_verify = replicas or Replica.objects\
                                            .filter(verified=False)\
                                            .exclude(protocol='staging')

    for replica in replicas_to_verify:
        if getattr(settings, 'REDIS_VERIFY_MANAGER', False):
            last_verification = r.hget('replicas_last_verified', replica.id)
            if last_verification is None or \
               time.time() - float(last_verification) >\
               getattr(settings, 'REDIS_VERIFY_DELAY', 86400):
                verify_replica.delay(replica.id)
                r.hset('replicas_last_verified', replica.id, time.time())
                r.hincrby('replicas_verification_attempts', replica.id)
                if r.hget('replicas_verification_attempts', replica.id) > 3:
                    r.sadd('replicas_manual_verification', replica.id)
        else:
            verify_replica.delay(replica.id)


@task(name="tardis_portal.verify_replica", ignore_result=True)
def verify_replica(replica_id, only_local=False, reverify=False):
    '''
    verify task
    allowemtpychecksums is false for auto-verify, hence the parameter
    '''
    from tardis.tardis_portal.models import Replica
    # Use a transaction for safety
    with transaction.commit_on_success():
        # Get replica locked for write (to prevent concurrent actions)
        replica = Replica.objects.select_for_update().get(id=replica_id)
        if replica.stay_remote or replica.is_local():
            # Check after lock (concurrency paranoia)
            if not replica.verified or reverify:
                replica.verify()
                replica.save(update_fields=['verified'])
        else:
            # Check after lock (concurrency paranoia)
            if not replica.is_local() and not only_local:
                stage_replica(replica)


@task(name="tardis_portal.create_staging_datafiles", ignore_result=True)
def create_staging_datafiles(files, user_id, dataset_id, is_secure):

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
    from tardis.tardis_portal.models import DataFile, Dataset, Replica, \
        Location
    dataset = Dataset.objects.get(id=dataset_id)

    url, size = get_staging_url_and_size(username, filepath)
    datafile = DataFile(dataset=dataset,
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
