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
                        (r'^test/experiment/view/(?P<experiment_id>\d+)/$',
                         'tardis.tardis_portal.views.view_experiment'),
                        (r'^test/download/datafile/(?P<datafile_id>\d+)/$',
                         'tardis.tardis_portal.download.download_datafile'),
                        (r'^test/vbl/download/datafile/(?P<datafile_id>\d+)/$',
                         'tardis.tardis_portal.tests.mock_vbl_download.download_datafile'),
                        (r'^test/ExperimentImage/load/(?P<parameter_id>\d+)/$',
                         'tardis.tardis_portal.views.load_experiment_image'),
                        (r'^test/DatasetImage/load/(?P<parameter_id>\d+)/$',
                         'tardis.tardis_portal.views.load_dataset_image'),
                        (r'^test/DatafileImage/load/(?P<parameter_id>\d+)/$',
                         'tardis.tardis_portal.views.load_datafile_image'),
    (r'^test/experiment/view/(?P<experiment_id>\d+)/$', 'tardis.tardis_portal.views.view_experiment'),
    (r'^test/download/datafile/(?P<datafile_id>\d+)/$', 'tardis.tardis_portal.download.download_datafile'),
    (r'^test/vbl/download/datafile/(?P<datafile_id>\d+)/$', 'tardis.tardis_portal.tests.mock_vbl_download.download_datafile'),
)
