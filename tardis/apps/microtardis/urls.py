from django.conf.urls.defaults import patterns
from tardis.urls import urlpatterns as tardisurls
from django.conf import settings

# Use the new views in MicroTardis
urlpatterns = patterns('tardis.apps.microtardis.views',
    (r'^thumbnails/(?P<size>[\w\.]+)/(?P<datafile_id>[\w\.]+)/$', 'display_thumbnails'),
    (r'^ajax/parameters/(?P<dataset_file_id>\d+)/$', 'retrieve_parameters'),
    (r'^spectrum_csv/(?P<datafile_id>\d+)/$', 'get_spectrum_csv'),
    (r'^spectrum_json/(?P<datafile_id>\d+)/$', 'get_spectrum_json'),
    (r'^(?P<datafile_id>\d+)/$', 'direct_to_thumbnail_html'),
)

# Media for MicroTardis
urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MT_STATIC_DOC_ROOT}),
)

# Use the new templates in MicroTardis but still use the original views in MyTardis
urlpatterns += patterns('tardis.tardis_portal.views',
    (r'^ajax/datafile_list/(?P<dataset_id>\d+)/$', 'retrieve_datafile_list', {'template_name': 'datafile_list_mt.html'}),
)

# Include all the URL patterns in MyTardis
urlpatterns += tardisurls