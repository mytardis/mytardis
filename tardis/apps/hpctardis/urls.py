from django.conf.urls.defaults import patterns
from tardis.urls import urlpatterns as tardisurls
from django.conf import settings

# Create the hpcardis links
urlpatterns = patterns('tardis.apps.hpctardis.views',
    (r'^rif_cs/$','rif_cs'),
    (r'^publishauth/$','auth_exp_publish'),
    (r'^apps/hpctardis/protocol/$','protocol'),
    (r'^apps/hpctardis/login/$','login'),
    (r'^apps/addfiles/$','addfiles'),
)
  
  
# Media for MicroTardis
urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.HPC_STATIC_DOC_ROOT}),
)
  
# Add links that will override existing tardis links
urlpatterns += patterns('tardis.apps.hpctardis.views',
                        (r'^experiment/view/(?P<experiment_id>\d+)/publish/$', 
                            'publish_experiment'))    

# Add remaining tardis links
urlpatterns += tardisurls
