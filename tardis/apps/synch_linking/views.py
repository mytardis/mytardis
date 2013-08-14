'''
retrieve dataset url by mongodb id in dataset parameter set
'''
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from tardis.tardis_portal.models.parameters import DatasetParameter
from tardis.tardis_portal.models.parameters import DatasetParameterSet
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema


def url_by_id(request, mongodb_id):
    schema_name = getattr(settings, "SYNCH_DS_SCHEMANAME",
                          "http://synchrotron.org.au/mx/indexed/1")
    schema = Schema.objects.get(namespace=schema_name, type=Schema.DATASET)

    parameter_string = getattr(settings, "SYNCH_MONGODB_ID_NAME", "ID")
    parameter_name = ParameterName.objects.get(schema=schema,
                                               name=parameter_string)

    dsp_s = DatasetParameterSet.objects.filter(schema=schema)

    for dsp in dsp_s:
        try:
            parameter = DatasetParameter.objects.get(
                parameterset=dsp, name=parameter_name)
            if parameter.get().strip() == mongodb_id.strip():
                ds_url = reverse('tardis.tardis_portal.views.view_dataset',
                                 kwargs={'dataset_id': dsp.dataset.id})
                if request.GET.get("redirect", False):
                    return HttpResponseRedirect(ds_url)
                return HttpResponse(ds_url)
        except DatasetParameter.DoesNotExist:
            pass
    return None
