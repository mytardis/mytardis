"""
Additions to MyTardis's REST API
"""
from django.conf.urls import url
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

from tastypie.utils import trailing_slash

import tardis.tardis_portal.api
from tardis.tardis_portal.auth.decorators import has_datafile_download_access
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFileObject

from .check import dfo_online
from .tasks import dfo_recall


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
                self.wrap_view('dfo_online'), name="hsm_api_dfo_online"),
        ]

    def recall_dfo(self, request, **kwargs):
        '''
        Recall archived DataFileObject from HSM system
        '''
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

        dfo_recall.apply_async(
            args=[dfo.id, request.user.id],
            priority=dfo.priority)

        response = HttpResponse()
        return response

    def dfo_online(self, request, **kwargs):
        '''
        Return the online status of a DataFileObject stored in a
        Hierarchical Storage Management (HSM) system
        '''
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

        return JsonResponse({'online': dfo_online(dfo)})


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
        ]

    def online_count(self, request, **kwargs):
        '''
        Return the number of online files and the total number of files in a
        dataset stored in a Hierarchical Storage Management (HSM) system
        '''
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        dataset = Dataset.objects.get(id=kwargs['pk'])

        return JsonResponse({
            'online_files': dataset.online_files_count,
            'total_files': dataset.datafile_set.count()
        })
