from django.urls import re_path

from . import views

app_name = "tardis.apps.publication_workflow"

urlpatterns = [
    re_path(r'^form/$', views.form_view,
        name='tardis.apps.publication_workflow.views.form_view'),
    re_path(r'^data/fetch_experiments_and_datasets/$', views.fetch_experiments_and_datasets,
        name='tardis.apps.publication_workflow.views.fetch_experiments_and_datasets'),
    re_path(r'^my-publications/$', views.my_publications,
        name='my_publications'),
    re_path(r'^draft_pubs_list/$', views.retrieve_draft_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_draft_pubs_list'),
    re_path(r'^scheduled_pubs_list/$', views.retrieve_scheduled_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_scheduled_pubs_list'),
    re_path(r'^released_pubs_list/$', views.retrieve_released_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_released_pubs_list'),
    re_path(r'^retracted_pubs_list/$', views.retrieve_retracted_pubs_list,
        name='tardis.apps.publication_workflow.views.retrieve_retracted_pubs_list'),
    re_path(r'^tokens/(?P<experiment_id>\d+)/$', views.tokens,
        name='tardis.apps.publication_workflow.views.tokens'),
    re_path(r'^tokens_json/(?P<experiment_id>\d+)/$', views.retrieve_access_list_tokens_json,
        name='tardis.apps.publication_workflow.views.retrieve_access_list_tokens_json'),
    re_path(r'^experiment/(?P<experiment_id>\d+)/is_publication/$', views.is_publication,
        name='tardis.apps.publication_workflow.views.is_publication'),
    re_path(r'^experiment/(?P<experiment_id>\d+)/is_publication_draft/$', views.is_publication_draft,
        name='tardis.apps.publication_workflow.views.is_publication_draft'),
    re_path(r'^publication/delete/(?P<experiment_id>\d+)/$', views.delete_publication,
        name='tardis.apps.publication_workflow.views.delete_publication'),
    re_path(r'^publication/retract/(?P<publication_id>\d+)/$', views.retract_publication,
        name='tardis.apps.publication_workflow.views.retract_publication'),
    re_path(r'^publication/mint_doi/(?P<experiment_id>\d+)/$', views.mint_doi_and_deactivate,
         name='tardis.apps.publication_workflow.views.mint_doi_and_deactivate'),
    re_path(r'^licenses', views.get_licenses,
        name='tardis.apps.publication_workflow.views.get_licenses')
]
