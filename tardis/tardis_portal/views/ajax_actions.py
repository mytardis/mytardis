"""
views that perform some action and don't return anything very useful
"""

import json
import logging

from celery import group, chord
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.cache import never_cache

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.auth.decorators import has_dataset_write
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.tasks import (
    cache_done_notify, create_staging_datafiles)

logger = logging.getLogger(__name__)


@never_cache
@authz.dataset_download_required
def cache_dataset(request, dataset_id=None, notify=True):
    dataset = Dataset.objects.get(id=dataset_id)
    run_this = group(df.cache_file.s()
                     for df in dataset.datafile_set.all())
    if notify:
        run_this = chord(run_this)(
            cache_done_notify.subtask(kwargs={
                'user_id': request.user.id,
                'site_id': Site.objects.get_current(request).id,
                'ct_id': ContentType.objects.get_for_model(Dataset).id,
                'obj_ids': [dataset_id], }))
    if hasattr(run_this, 'apply_async'):
        result = run_this.apply_async()
    else:
        result = run_this
    return HttpResponse(json.dumps({"result": str(result.id)}),
                        content_type='application/json')


@login_required
def stage_files_to_dataset(request, dataset_id):
    """
    Takes a JSON list of filenames to import from the staging area to this
    dataset.
    """
    if not has_dataset_write(request, dataset_id):
        return HttpResponseForbidden()

    if request.method != 'POST':
        # This method only accepts POSTS, so send 405 Method Not Allowed
        response = HttpResponse(status=405)
        response['Allow'] = 'POST'
        return response

    user = request.user

    # Incoming data MUST be JSON
    if not request.META['CONTENT_TYPE'].startswith('application/json'):
        return HttpResponse(status=400)

    try:
        files = json.loads(request.body)
    except:
        return HttpResponse(status=400)

    create_staging_datafiles.delay(files, user.id, dataset_id,
                                   request.is_secure())

    email = {'email': user.email}
    return HttpResponse(json.dumps(email), status=201)
