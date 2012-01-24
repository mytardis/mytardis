from django.conf.urls.defaults import patterns
from tardis.urls import urlpatterns as tardisurls
from django.conf import settings

# Create the hpcardis links
urlpatterns = patterns('tardis.apps.hpctardis.views',
    (r'^rif_cs/$','rif_cs'),
    (r'^publishauth/$','auth_exp_publish'),
    (r'^apps/hpctardis/protocol/$','protocol'),
    (r'^apps/hpctardis/login/$','login'),
    (r'^apps/hpctardis/addfiles/$','addfiles'),
)
  
  
# Media for MicroTardis
urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.HPC_STATIC_DOC_ROOT}),
)
  
# Add links that will override existing tardis links
urlpatterns += patterns('tardis.apps.hpctardis.views',
                        (r'^experiment/view/(?P<experiment_id>\d+)/publish/$', 
                            'publish_experiment'))    
urlpatterns += patterns(
    'tardis.apps.hpctardis.download',
    (r'^download/datafile/(?P<datafile_id>\d+)/$', 'download_datafile'),
    (r'^download/experiment/(?P<experiment_id>\d+)/(?P<comptype>[a-z]{3})/$',
     'download_experiment_alt'),
    (r'^download/datafiles/$', 'download_datafiles'),
    (r'^download/datafile/ws/$', 'download_datafile_ws'),
    )


# Add remaining tardis links
urlpatterns += tardisurls
