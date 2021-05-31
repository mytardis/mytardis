from django.conf.urls import url

from . import views
app_name = "tardis.apps.publication_workflow"

urlpatterns = [
    url(r'^form/$', views.form_view,
        name='tardis.apps.publication_workflow.views.form_view'),
    url(r'^data/fetch_experiments_and_datasets/$', views.fetch_experiments_and_datasets,
        name='tardis.apps.publication_workflow.views.fetch_experiments_and_datasets'),
    url(r'^my-publications/$', views.my_publications,
        name='my_publications'),
    url(r'^draft_pubs_list/$', views.retrieve_draft_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_draft_pubs_list'),
    url(r'^scheduled_pubs_list/$', views.retrieve_scheduled_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_scheduled_pubs_list'),
    url(r'^released_pubs_list/$', views.retrieve_released_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_released_pubs_list'),
    url(r'^retracted_pubs_list/$', views.retrieve_retracted_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_retracted_pubs_list'),
    url(r'^tokens/(?P<experiment_id>\d+)/$', views.tokens,
        name='tardis.apps.publication_workflow.views.tokens'),
    url(r'^tokens_json/(?P<experiment_id>\d+)/$', views.retrieve_access_list_tokens_json,
        name='tardis.apps.publication_workflow.views.retrieve_access_list_tokens_json'),
    url(r'^experiment/(?P<experiment_id>\d+)/is_publication/$', views.is_publication,
        name='tardis.apps.publication_workflow.views.is_publication'),
    url(r'^experiment/(?P<experiment_id>\d+)/is_publication_draft/$', views.is_publication_draft,
        name='tardis.apps.publication_workflow.views.is_publication_draft'),
    url(r'^publication/delete/(?P<experiment_id>\d+)/$', views.delete_publication,
        name='tardis.apps.publication_workflow.views.delete_publication'),
    url(r'^publication/retract/(?P<publication_id>\d+)/$', views.retract_publication,
        name='tardis.apps.publication_workflow.views.retract_publication'),
    url(r'^publication/mint_doi/(?P<experiment_id>\d+)/$', views.mint_doi_and_deactivate,
         name='tardis.apps.publication_workflow.views.mint_doi_and_deactivate')
]
