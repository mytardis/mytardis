# pylint: disable=http-response-with-json-dumps,http-response-with-content-type-json
"""
views that perform some action and don't return anything very useful
"""

import json
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from celery import chord, group

from ..auth import decorators as authz
from ..models import Dataset
from ..tasks import cache_done_notify

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
                'priority': settings.DEFAULT_EMAIL_TASK_PRIORITY,
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
