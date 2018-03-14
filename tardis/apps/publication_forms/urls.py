from django.conf.urls import url

from .pub_form_config import PubFormConfig

from .views import (
    index,
    fetch_experiments_and_datasets,
    pdb_helper,
    approval_view
)

urlpatterns = [
    url(r'^form/$', index, name='tardis.apps.publication_forms.views.index'),
    url(r'^data/fetch_experiments_and_datasets/$',
        fetch_experiments_and_datasets,
        name='tardis.apps.publication_forms.views.fetch_experiments_and_datasets'),
    url(r'^helper/pdb/(?P<pdb_id>.*)/$',
        pdb_helper, name='tardis.apps.publication_forms.views.pdb_helper'),
    url(r'^approvals/$', approval_view,
        name='tardis.apps.publication_forms.views.approval_view'),
]

# one-time settings check
PubFormConfig().do_setup()
