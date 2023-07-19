"""
Additions to MyTardis's REST API
"""
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import re_path

from tastypie.utils import trailing_slash

import tardis.tardis_portal.api
from tardis.tardis_portal.auth.decorators import has_download_access
from tardis.tardis_portal.models.datafile import DataFileObject

from .utils import generate_presigned_url


class ReplicaAppResource(tardis.tardis_portal.api.ReplicaResource):
    """Extends MyTardis's API for DFOs, adding in a download method
    for S3 objects
    """

    class Meta(tardis.tardis_portal.api.ReplicaResource.Meta):
        # This will be mapped to s3utils_replica by MyTardis's urls.py:
        resource_name = "replica"
        authorization = tardis.tardis_portal.api.ACLAuthorization()
        queryset = DataFileObject.objects.all()

    def prepend_urls(self):
        return [
            re_path(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/download%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("download_dfo"),
                name="s3_api_download_dfo",
            )
        ]

    def download_dfo(self, request, **kwargs):
        """
        Download DataFileObject from S3 Object Store
        """
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)
        self.throttle_check(request)

        dfo = DataFileObject.objects.get(id=kwargs["pk"])
        if not has_download_access(
            request=request, obj_id=dfo.datafile.id, ct_type="datafile"
        ):
            return HttpResponseForbidden()

        self.authorized_read_detail(
            [dfo.datafile], self.build_bundle(obj=dfo.datafile, request=request)
        )

        s3_url = generate_presigned_url(dfo)

        # Redirect to Object Store:
        response = redirect(s3_url)
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            dfo.datafile.filename
        )
        return response
