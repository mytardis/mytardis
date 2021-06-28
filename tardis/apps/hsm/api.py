"""
Additions to MyTardis's REST API
"""
import logging
from django.conf import settings
from django.conf.urls import url
from django.core.mail import get_connection, EmailMessage
from django.http import (HttpResponseForbidden,
                         HttpResponseServerError,
                         JsonResponse)

from tastypie.utils import trailing_slash

import tardis.tardis_portal.api
from tardis.tardis_portal.auth.decorators import has_datafile_download_access, has_dataset_download_access
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFileObject

from .check import dfo_online
from .email_text import email_dataset_recall_requested
from .tasks import dfo_recall

logger = logging.getLogger(__name__)


class ReplicaAppResource(tardis.tardis_portal.api.ReplicaResource):
    '''Extends MyTardis's API for DFOs, adding in a recall method and an online
    check method for files in a Hierarchical Storage Management (HSM) system
    '''

    class Meta(tardis.tardis_portal.api.ReplicaResource.Meta):
        # This will be mapped to hsm_replica by MyTardis's urls.py:
        resource_name = 'replica'
        authorization = tardis.tardis_portal.api.ACLAuthorization()
        queryset = DataFileObject.objects.all()

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/recall%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('recall_dfo'), name="hsm_api_recall_dfo"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/online%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dfo_is_online'), name="hsm_api_dfo_online"),
        ]

    def dfo_is_online(self, request, **kwargs):
        '''
        Return the online status of a DataFileObject stored in a
        Hierarchical Storage Management (HSM) system
        '''
        from .exceptions import HsmException

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        dfo = DataFileObject.objects.get(id=kwargs['pk'])
        if not has_datafile_download_access(
                request=request, datafile_id=dfo.datafile.id):
            return HttpResponseForbidden()

        self.authorized_read_detail(
            [dfo.datafile],
            self.build_bundle(obj=dfo.datafile, request=request))

        try:
            online_status = dfo_online(dfo)
            return JsonResponse({'online': online_status})
        except HsmException as err:
            logger.error("Status failed for DFO %s: %s" % (dfo.id, str(err)))
            return JsonResponse({
                "error_message":
                    "Recall failed for DFO %s: %s" % (dfo.id, type(err).__name__)
            }, status=HttpResponseServerError.status_code)

        return HttpResponseServerError()

    def recall_dfo(self, request, **kwargs):
        '''
        Recall archived DataFileObject from HSM system
        '''
        from .exceptions import HsmException

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        dfo = DataFileObject.objects.get(id=kwargs['pk'])
        if not has_datafile_download_access(
                request=request, datafile_id=dfo.datafile.id):
            return HttpResponseForbidden()

        self.authorized_read_detail(
            [dfo.datafile],
            self.build_bundle(obj=dfo.datafile, request=request))

        try:
            dfo_recall.apply_async(
                args=[dfo.id, request.user.id],
                priority=dfo.priority)
        except HsmException as err:
            # We would only see an exception here if CELERY_TASK_ALWAYS_EAGER is
            # True, making the task run synchronously
            logger.error("Recall failed for DFO %s: %s" % (dfo.id, str(err)))
            return JsonResponse({
                "error_message":
                    "Recall failed for DFO %s: %s" % (dfo.id, type(err).__name__)
            }, status=HttpResponseServerError.status_code)

        # Log recall event
        if getattr(settings, "ENABLE_EVENTLOG", False):
            from tardis.apps.eventlog.utils import log
            log(
                action="RECALL",
                extra={
                    "type": "datafile",
                    "id": dfo.datafile.id
                },
                request=request
            )

        return JsonResponse({
            "message": "Recall requested for DFO %s" % dfo.id
        })


class DatasetAppResource(tardis.tardis_portal.api.DatasetResource):
    '''Extends MyTardis's API for Datasets, adding in a method to count
    online files in a Hierarchical Storage Management (HSM) system
    '''

    class Meta(tardis.tardis_portal.api.DatasetResource.Meta):
        # This will be mapped to hsm_dataset by MyTardis's urls.py:
        resource_name = 'dataset'
        authorization = tardis.tardis_portal.api.ACLAuthorization()
        queryset = Dataset.objects.all()

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/count%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('online_count'),
                name="hsm_api_count_online_files"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/recall%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dataset_recall'), name="hsm_api_dataset_recall"),
        ]

    def online_count(self, request, **kwargs):
        '''
        Return the number of online files and the total number of files in a
        dataset stored in a Hierarchical Storage Management (HSM) system
        '''
        from .exceptions import HsmException

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        dataset = Dataset.objects.get(id=kwargs['pk'])

        try:
            online_files = dataset.online_files_count
            total_files = dataset.datafile_set.count()
            return JsonResponse({
                'online_files': online_files,
                'total_files': total_files
            })
        except HsmException as err:
            logger.error("Status failed for DS %s: %s" % (dataset.id, str(err)))
            return JsonResponse({
                "error_message":
                    "Status failed for DS %s: %s" % (dataset.id, type(err).__name__)
            }, status=HttpResponseServerError.status_code)

        return HttpResponseServerError()

    def dataset_recall(self, request, **kwargs):
        """
        Send and email to Site admin to recall Dataset from HSM system
        """
        from .exceptions import HsmException

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        ds = Dataset.objects.get(id=kwargs['pk'])
        if not has_dataset_download_access(
                request=request, dataset_id=ds.id):
            return HttpResponseForbidden()

        """
        send an email to MyTardis admin
        """
        try:
            subject, content = email_dataset_recall_requested(ds, request.user)
            logger.info("sending email to %s", settings.RDSM_SUPPORT_EMAIL)
            email = EmailMessage(subject, content, to=[settings.RDSM_SUPPORT_EMAIL], cc=[request.user.email],
                                 from_email=settings.SUPPORT_EMAIL, connection=get_connection(fail_silently=True))
            email.send(fail_silently=True)
        except HsmException as err:
            logger.error("Recall failed for DS %s: %s" % (ds.id, str(err)))
            return JsonResponse({
                "error_message":
                    "Recall failed for DS %s: %s" % (ds.id, type(err).__name__)
            }, status=HttpResponseServerError.status_code)

        # Log recall event
        if getattr(settings, "ENABLE_EVENTLOG", False):
            from tardis.apps.eventlog.utils import log
            log(
                action="RECALL",
                extra={
                    "type": "dataset",
                    "id": ds.id
                },
                request=request
            )

        return JsonResponse({
            "message": "Recall requested for Dataset %s" % ds.id
        })
