from django.conf.urls import url

from .views import (
    form_view,
    fetch_experiments_and_datasets,
    my_publications,
    retrieve_draft_pubs_list,
    retrieve_scheduled_pubs_list,
    retrieve_released_pubs_list,
    tokens,
    retrieve_access_list_tokens_json,
    is_publication,
    is_publication_draft,
    delete_publication,
    mint_doi_and_deactivate
)

urlpatterns = [
    url(r'^form/$', form_view,
        name='tardis.apps.publication_workflow.views.form_view'),
    url(r'^data/fetch_experiments_and_datasets/$', fetch_experiments_and_datasets,
        name='tardis.apps.publication_workflow.views.fetch_experiments_and_datasets'),
    url(r'^my_publications/$', my_publications,
        name='tardis.apps.publication_workflow.views.my_publications'),
    url(r'^draft_pubs_list/$', retrieve_draft_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_draft_pubs_list'),
    url(r'^scheduled_pubs_list/$', retrieve_scheduled_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_scheduled_pubs_list'),
    url(r'^released_pubs_list/$', retrieve_released_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_released_pubs_list'),
    url(r'^tokens/(?P<experiment_id>\d+)/$', tokens,
        name='tardis.apps.publication_workflow.views.tokens'),
    url(r'^tokens_json/(?P<experiment_id>\d+)/$', retrieve_access_list_tokens_json,
        name='tardis.apps.publication_workflow.views.retrieve_access_list_tokens_json'),
    url(r'^experiment/(?P<experiment_id>\d+)/is_publication/$', is_publication,
        name='tardis.apps.publication_workflow.views.is_publication'),
    url(r'^experiment/(?P<experiment_id>\d+)/is_publication_draft/$', is_publication_draft,
        name='tardis.apps.publication_workflow.views.is_publication_draft'),
    url(r'^publication/delete/(?P<experiment_id>\d+)/$', delete_publication,
        name='tardis.apps.publication_workflow.views.delete_publication'),
    url(r'^publication/mint_doi/(?P<experiment_id>\d+)/$', mint_doi_and_deactivate,
         name='tardis.apps.publication_workflow.views.mint_doi_and_deactivate')
]
