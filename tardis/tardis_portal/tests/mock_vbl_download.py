from django.http import HttpResponse
from django.template import Template, RequestContext


def download_datafile(request, *args, **kwargs):
    "Dummy view for vbl download tests"
    t = Template(template_string='')
    c = RequestContext(request, {})
    return HttpResponse(t.render(c))
