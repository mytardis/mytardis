from celery.task import task
from django.db import transaction

from tardis.tardis_portal.staging import stage_replica
from tardis.tardis_portal.models import Replica

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

