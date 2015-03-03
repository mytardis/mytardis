from django.conf.urls import patterns

urlpatterns = patterns(
    'tardis.apps.filepicker',
    (r'^upload_button/(?P<dataset_id>\d+)/$', 'views.upload_button'),
    (r'^fpupload/(?P<dataset_id>\d+)/$', 'views.fpupload'),
)
