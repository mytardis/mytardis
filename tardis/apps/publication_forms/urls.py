from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
                       (r'^form/$', 'tardis.apps.publication_forms.views.index'),
                       (r'^data/fetch_experiments_and_datasets/$', 'tardis.apps.publication_forms.views.fetch_experiments_and_datasets'),
                      )
