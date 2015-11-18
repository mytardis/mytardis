"""
views that return JSON data
"""

import json
import logging

from django.forms import model_to_dict
from django.http import HttpResponseNotFound, HttpResponseForbidden, \
    HttpResponse
from django.views.decorators.cache import never_cache

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.models import Dataset, Experiment, License
from tardis.tardis_portal.shortcuts import return_response_not_found
from tardis.tardis_portal.views.utils import HttpResponseMethodNotAllowed
from tardis.tardis_portal.views.utils import get_dataset_info

logger = logging.getLogger(__name__)


@never_cache  # too complex # noqa
@authz.dataset_access_required
def dataset_json(request, experiment_id=None, dataset_id=None):
    # Experiment ID is optional (but dataset_id is not)!
    dataset = Dataset.objects.get(id=dataset_id)

    if experiment_id:
        try:
            # PUT is fine for non-existing resources, but GET/DELETE is not
            if request.method == 'PUT':
                experiment = Experiment.objects.get(id=experiment_id)
            else:
                experiment = dataset.experiments.get(id=experiment_id)
        except Experiment.DoesNotExist:
            return HttpResponseNotFound()

    # Convenience methods for permissions
    def can_update():
        return authz.has_dataset_ownership(request, dataset_id)
    can_delete = can_update

    def add_experiments(updated_experiments):
        current_experiments = \
            frozenset(dataset.experiments.values_list('id', flat=True))
        # Get all the experiments that currently aren't associated
        for experiment_id in updated_experiments - current_experiments:
            # You must own the experiment to assign datasets to it
            if authz.has_experiment_ownership(request, experiment_id):
                experiment = Experiment.safe.get(request.user, experiment_id)
                logger.info("Adding dataset #%d to experiment #%d" %
                            (dataset.id, experiment.id))
                dataset.experiments.add(experiment)

    # Update this experiment to add it to more experiments
    if request.method == 'PUT':
        # Obviously you can't do this if you don't own the dataset
        if not can_update():
            return HttpResponseForbidden()
        data = json.loads(request.body)
        # Detect if any experiments are new, and add the dataset to them
        add_experiments(frozenset(data['experiments']))
        # Include the experiment we PUT to, as it may also be new
        if experiment is not None:
            add_experiments(frozenset((experiment.id,)))
        dataset.save()

    # Remove this dataset from the given experiment
    if request.method == 'DELETE':
        # First, we need an experiment
        if experiment_id is None:
            # As the experiment is in the URL, this method will never be
            # allowed
            if can_update():
                return HttpResponseMethodNotAllowed(allow="GET PUT")
            return HttpResponseMethodNotAllowed(allow="GET")
        # Cannot remove if this is the last experiment or if it is being
        # removed from a publication
        if (not can_delete() or dataset.experiments.count() < 2 or
           experiment.is_publication()):
            return HttpResponseForbidden()
        dataset.experiments.remove(experiment)
        dataset.save()

    has_download_permissions = \
        authz.has_dataset_download_access(request, dataset_id)

    return HttpResponse(json.dumps(get_dataset_info(dataset,
                                                    has_download_permissions)),
                        content_type='application/json')


@never_cache
@authz.experiment_access_required
def experiment_datasets_json(request, experiment_id):
    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    has_download_permissions = \
        authz.has_experiment_download_access(request, experiment_id)

    objects = [
        get_dataset_info(ds, include_thumbnail=has_download_permissions,
                         exclude=['datafiles'])
        for ds in experiment.datasets.all().order_by('description')]

    return HttpResponse(json.dumps(objects), content_type='application/json')


def retrieve_licenses(request):
    try:
        type_ = int(request.REQUEST['public_access'])
        licenses = License.get_suitable_licenses(type_)
    except KeyError:
        licenses = License.get_suitable_licenses()
    return HttpResponse(json.dumps([model_to_dict(x) for x in licenses]))
