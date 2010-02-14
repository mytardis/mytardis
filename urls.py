from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import login, logout
from registration.forms import RegistrationFormUniqueEmail

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'tardis.tardis_portal.views.index'),		
	(r'^about/$', 'tardis.tardis_portal.views.about'),	
	(r'^partners/$', 'tardis.tardis_portal.views.partners'),
	(r'^deposit/$', 'tardis.tardis_portal.views.deposit'),
	(r'^schema/$', 'tardis.tardis_portal.views.deposit'),	
	(r'^orca/$', 'tardis.tardis_portal.views.orca'),
	(r'^news/$', 'tardis.tardis_portal.views.news'),
	(r'^experiment/approve/$', 'tardis.tardis_portal.views.approve_experiment'),	
	(r'^experiment/view/(?P<experiment_id>\d+)/$', 'tardis.tardis_portal.views.view_experiment'),
	(r'^experiment/view/$', 'tardis.tardis_portal.views.experiment_index'),				
	(r'^experiment/register/$', 'tardis.tardis_portal.views.register_experiment_ws_xmldata'),	
	(r'^experiment/view/(\d+)/download/$', 'tardis.tardis_portal.views.download'),	
	(r'^search/experiment/$', 'tardis.tardis_portal.views.search_experiment'),	
	(r'^search/datafile/$', 'tardis.tardis_portal.views.search_datafile'),	
	(r'^search/quick/$', 'tardis.tardis_portal.views.search_quick'),
	(r'^downloadTar/$', 'tardis.tardis_portal.views.downloadTar'),	
	(r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/add/(?P<username>\w+)$', 'tardis.tardis_portal.views.add_access_experiment'),
	(r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/remove/(?P<username>\w+)$', 'tardis.tardis_portal.views.remove_access_experiment'),		
	(r'^experiment/control_panel/(?P<experiment_id>\d+)/access_list/$', 'tardis.tardis_portal.views.retrieve_access_list'),		
	(r'^experiment/control_panel/$', 'tardis.tardis_portal.views.control_panel'),		
	(r'^ajax/parameters/(?P<dataset_file_id>\d+)/$', 'tardis.tardis_portal.views.retrieve_parameters'),
	(r'^ajax/xml_data/(?P<dataset_file_id>\d+)/$', 'tardis.tardis_portal.views.retrieve_xml_data'),	
	(r'^ajax/datafile_list/(?P<dataset_id>\d+)/$', 'tardis.tardis_portal.views.retrieve_datafile_list'),
	(r'^ajax/ftp/(?P<id>\d+)/$', 'tardis.tardis_portal.views.retrieve_ftp'),	
	(r'^ajax/user_list/$', 'tardis.tardis_portal.views.retrieve_user_list'),
	(r'^login/$',  login, {'template_name': 'tardis_portal/registration/login.html'}),
	(r'^accounts/login/$',  login, {'template_name': 'tardis_portal/registration/login.html'}),	
	(r'^logout/$', logout, {'next_page': '/'}),	
	(r'^accounts/register/', include('registration.urls'),{'form_class':RegistrationFormUniqueEmail}),
	(r'^accounts/', include('registration.urls')),	
	(r'site_media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': settings.STATIC_DOC_ROOT}),
	(r'media/(?P<path>.*)$', 'django.views.static.serve',
	        {'document_root': settings.ADMIN_MEDIA_STATIC_DOC_ROOT}),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
