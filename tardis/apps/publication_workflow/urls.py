from django.conf.urls import patterns

from .pub_form_config import PubFormConfig

urlpatterns = patterns(
    '',
    (r'^form/$', 'tardis.apps.publication_workflow.views.index'),
    (r'^data/fetch_experiments_and_datasets/$',
     'tardis.apps.publication_workflow.views.fetch_experiments_and_datasets'),
    (r'^helper/pdb/(?P<pdb_id>.*)/$',
     'tardis.apps.publication_workflow.views.pdb_helper'),
    (r'^approvals/$', 'tardis.apps.publication_workflow.views.approval_view'),
)

# one-time settings check
PubFormConfig().do_setup()
