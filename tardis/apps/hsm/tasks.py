"""
Tasks for recalling data from tape in
Hierarchical Storage Management (HSM) systems
"""
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from tardis.celery import tardis_app
from .email_text import email_dfo_recall_complete
from .email_text import email_dfo_recall_failed

logger = logging.getLogger(__name__)


@tardis_app.task(name='hsm.dfo.recall', ignore_result=True)
def dfo_recall(dfo_id, user_id):
    '''
    Recall file from archive (tape) and notify the user who
    requested the recall by email
    '''
    from tardis.tardis_portal.models import DataFileObject
    dfo = DataFileObject.objects.get(id=dfo_id)
    # Attempt to read the first bit of the file to force it
    # to be recalled to disk:
    try:
        dfo.file_object.read(1024)
        recalled = True
        reason = None
    except IOError as err:
        recalled = False
        logger.error(
            "Recall failed for DFO ID: %s, User ID: %s with error:\n%s",
            dfo_id, user_id, str(err))

    if user_id:
        user = User.objects.get(id=user_id)
        if recalled:
            subject, content = email_dfo_recall_complete(dfo, user)
        else:
            subject, content = email_dfo_recall_failed(dfo, user)

        user.email_user(subject, content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        fail_silently=True)
        logger.info("DFO recall email sent for DFO ID %s, User ID %s",
                    dfo_id, user_id)


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
    online_files_param.string_value = "%s / %s" % (online_files,  total_files)
    online_files_param.save()

    updated_pname = ParameterName.objects.get(
        schema=schema, name='updated')
    updated_param, _ = DatasetParameter.objects.get_or_create(  # pylint: disable=W0633
        parameterset=pset, name=updated_pname)
    updated_param.datetime_value = timezone.localtime()
    updated_param.save()
