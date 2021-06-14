"""
Tasks for recalling data from tape in
Hierarchical Storage Management (HSM) systems
"""
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from tardis.celery import tardis_app
from .email_text import email_dfo_recall_complete, email_dfo_recall_requested
from .email_text import email_dfo_recall_failed
from .exceptions import HsmException

logger = logging.getLogger(__name__)


@tardis_app.task(name='hsm.dfo.recall', ignore_result=True)
def dfo_recall(dfo_id, user_id):
    '''
    Recall file from archive (tape) and notify the user who
    requested the recall by email

    The "recall" just attempts to read the first bit of the file which on
    most HSM systems will automatically trigger a recall.

    Raises
    ------
    DataFileObjectNotVerified
        If dfo is unverified
    StorageClassNotSupportedError
        If the `django_storage_class` for the StorageBox of the input
        DataFileObject is not supported
    '''
    from django.core.files.storage import get_storage_class
    from tardis.tardis_portal.models import DataFileObject
    from .exceptions import (DataFileObjectNotVerified,
                             StorageClassNotSupportedError)
    from .storage import HsmFileSystemStorage

    # send an email to user acknowledging received request
    """
    send an email to user
    """
    if user_id:
        user = User.objects.get(id=user_id)
        try:
            subject, content = email_dfo_recall_requested(dfo_id, user)
            logger.info("sending recall requested email to user %s" % user)
            user.email_user(subject, content,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            fail_silently=False)
        except HsmException as err:
            logger.error("Error sending email", str(err))

    dfo = DataFileObject.objects.get(id=dfo_id)

    if not dfo.verified:
        raise DataFileObjectNotVerified(
            "Cannot recall unverified DataFileObject: %s" % dfo.id)

    storage_class = get_storage_class(dfo.storage_box.django_storage_class)
    if not issubclass(storage_class, HsmFileSystemStorage):
        msg = (
            "You have tried to recall a DataFileObject with data in a "
            "StorageBox with an unsupported django_storage_class. The "
            "required django_storage_class is "
            "'tardis.apps.hsm.storage.HsmFileSystemStorage'."
        )
        raise StorageClassNotSupportedError(msg)

    # Attempt to read the first bit of the file to force it
    # to be recalled to disk:
    try:
        dfo.file_object.read(1024)
        recalled = True
    except IOError as err:
        recalled = False
        logger.error(
            "Recall failed for DFO ID: %s, User ID: %s with error:\n%s",
            dfo_id, user_id, str(err))
    finally:
        dfo.file_object.close()

    if user_id:
        user = User.objects.get(id=user_id)
        if recalled:
            logger.info("sending recall complete email to %s", user.email)
            subject, content = email_dfo_recall_complete(dfo, user)
        else:
            logger.info("sending recall failed email to %s", user.email)
            subject, content = email_dfo_recall_failed(dfo, user)

        user.email_user(subject, content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        fail_silently=True)


@tardis_app.task(name='hsm.ds.check', ignore_result=True)
def ds_check(ds_id):
    '''
    Check the online status of Dataset ID ds_id
    and record the results in Dataset metadata
    using the http://mytardis.org/schemas/hsm/dataset/1
    schema
    '''
    from tardis.tardis_portal.models.datafile import DataFile
    from tardis.tardis_portal.models.dataset import Dataset
    from tardis.tardis_portal.models.parameters import (Schema,
                                                        ParameterName,
                                                        DatasetParameterSet,
                                                        DatasetParameter)
    from .check import dataset_online_count

    dataset = Dataset.objects.get(id=ds_id)
    total_files = DataFile.objects.filter(dataset=dataset).count()
    online_files = dataset_online_count(dataset)

    # Assumes schema has been created by applying the migration
    # provided in the hsm app:
    schema = Schema.objects.get(
        namespace='http://mytardis.org/schemas/hsm/dataset/1')
    pset, _ = DatasetParameterSet.objects.get_or_create(
        schema=schema, dataset=dataset)

    online_files_pname = ParameterName.objects.get(
        schema=schema, name='online_files')
    online_files_param, _ = DatasetParameter.objects.get_or_create(  # pylint: disable=W0633
        parameterset=pset, name=online_files_pname)
    online_files_param.string_value = "%s / %s" % (online_files, total_files)
    online_files_param.save()

    updated_pname = ParameterName.objects.get(
        schema=schema, name='updated')
    updated_param, _ = DatasetParameter.objects.get_or_create(  # pylint: disable=W0633
        parameterset=pset, name=updated_pname)
    updated_param.datetime_value = timezone.localtime(timezone.now())
    updated_param.save()
