from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import HttpResponse
from django.template import Context

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.shortcuts import get_experiment_referer
from tardis.tardis_portal.shortcuts import render_response_index


@authz.dataset_access_required
def view_full_dataset(request, dataset_id):
    """Displays a MX Dataset and associated information.

    Shows a full (hundreds of images) dataset its metadata and a list
    of associated files with the option to show metadata of each file
    and ways to download those files.  With write permission this page
    also allows uploading and metadata editing.

    Settings for this view:
    INSTALLED_APPS += ("mx_views",)
    DATASET_VIEWS = [("http://synchrotron.org.au/views/dataset/full",
                      "tardis.apps.mx_views.views.view_full_dataset"),]

    """
    dataset = Dataset.objects.get(id=dataset_id)

    def get_datafiles_page():
        # pagination was removed by someone in the interface but not here.
        # need to fix.
        pgresults = 100

        paginator = Paginator(dataset.dataset_file_set.all(), pgresults)

        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.

        try:
            return paginator.page(page)
        except (EmptyPage, InvalidPage):
            return paginator.page(paginator.num_pages)

    c = Context({
        'dataset': dataset,
        'datafiles': get_datafiles_page(),
        'parametersets': dataset.getParameterSets()
                                .exclude(schema__hidden=True),
        'has_download_permissions':
            authz.has_dataset_download_access(request, dataset_id),
        'has_write_permissions':
            authz.has_dataset_write(request, dataset_id),
        'from_experiment': \
            get_experiment_referer(request, dataset_id),
        'other_experiments': \
            authz.get_accessible_experiments_for_dataset(request, dataset_id)
    })
    return HttpResponse(render_response_index(
        request, 'mx_views/view_full_dataset.html', c))
