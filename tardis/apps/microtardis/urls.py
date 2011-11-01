from django.conf.urls.defaults import patterns
from tardis.urls import urlpatterns as tardisurls

urlpatterns = patterns('tardis.apps.microtardis.views',
    (r'^ajax/parameters/(?P<dataset_file_id>\d+)/$', 'retrieve_parameters'),
    (r'^$', 'index_mt'),
    (r'^about/$', 'about_mt'),
    (r'^partners/$', 'partners_mt'),
)

urlpatterns += patterns('tardis.tardis_portal.views',
    (r'^experiment/view/(?P<experiment_id>\d+)/publish/$', 'publish_experiment', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^experiment/view/(?P<experiment_id>\d+)/$', 'view_experiment', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^experiment/view/$', 'experiment_index', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^experiment/create/$', 'create_experiment', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^experiment/search/$', 'search_experiment', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^experiment/control_panel/$', 'control_panel', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^stats/$', 'stats', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^groups/$', 'manage_groups', {'portal_template_name': 'portal_template_mt.html'}),
    (r'^login/$', 'login', {'portal_template_name': 'portal_template_mt.html'}),
    
)
urlpatterns += tardisurls
