from django.conf.urls import patterns, include, url

from .pub_form_config import PubFormConfig

urlpatterns = patterns(
    '',
    (r'^form/$', 'tardis.apps.publication_workflow.views.index'),
    (r'^data/fetch_experiments_and_datasets/$',
     'tardis.apps.publication_workflow.views.fetch_experiments_and_datasets'),
    (r'^approvals/$', 'tardis.apps.publication_workflow.views.approval_view'),
    (r'^my_publications/$',
     'tardis.apps.publication_workflow.views.my_publications'),
    (r'^draft_pubs_list/$',
     'tardis.apps.publication_workflow.views.retrieve_draft_pubs_list'),
    (r'^scheduled_pubs_list/$',
     'tardis.apps.publication_workflow.views.retrieve_scheduled_pubs_list'),
    (r'^released_pubs_list/$',
     'tardis.apps.publication_workflow.views.retrieve_released_pubs_list'),
    (r'^tokens/(?P<experiment_id>\d+)/$',
     'tardis.apps.publication_workflow.views.tokens'),
    (r'^tokens_json/(?P<experiment_id>\d+)/$',
     'tardis.apps.publication_workflow.views.retrieve_access_list_tokens_json'),
    (r'^experiment/(?P<experiment_id>\d+)/is_publication/$',
     'tardis.apps.publication_workflow.views.is_publication'),
    (r'^experiment/(?P<experiment_id>\d+)/is_publication_draft/$',
     'tardis.apps.publication_workflow.views.is_publication_draft'),
    (r'^publication/delete/(?P<experiment_id>\d+)/$',
     'tardis.apps.publication_workflow.views.delete_publication'),
    (r'^publication/mint_doi/(?P<experiment_id>\d+)/$',
      'tardis.apps.publication_workflow.views.mint_doi_and_deactivate')
)

# one-time settings check
PubFormConfig().do_setup()
