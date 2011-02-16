from django.conf.urls.defaults import patterns
from django.contrib.auth.urls import urlpatterns
from django.http import HttpResponse
from django.template import Template, RequestContext


def groups_view(request):
    "Dummy view for remote user tests"
    t = Template("Groups are {% for p, g in groups %}({{ p }},{{ g }}) {% endfor %}.")
    c = RequestContext(request, {'groups': request.groups})
    return HttpResponse(t.render(c))

# special urls for auth test cases
urlpatterns += patterns('',
    (r'^test/groups/$', groups_view),
)
