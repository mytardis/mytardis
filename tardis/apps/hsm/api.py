"""
Additions to MyTardis's REST API
"""
from django.conf.urls import url
from django.http import HttpResponse, HttpResponseForbidden

from tastypie.utils import trailing_slash

import tardis.tardis_portal.api
from tardis.tardis_portal.auth.decorators import has_datafile_download_access
from tardis.tardis_portal.models.datafile import DataFileObject

from .tasks import dfo_recall


class ReplicaAppResource(tardis.tardis_portal.api.ReplicaResource):
    '''Extends MyTardis's API for DFOs, adding in a recall method
    for files in a Hierarchical Storage Management (HSM) system
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
                self.wrap_view('recall_dfo'), name="hsm_api_recall_dfo")
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
