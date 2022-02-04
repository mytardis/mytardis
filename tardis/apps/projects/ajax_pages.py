from django.conf import settings
from django.views.decorators.cache import never_cache
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.shortcuts import render_response_index


@never_cache
# @authz.experiment_access_required
def project_latest_experiment(request, project_id):
    if settings.ONLY_EXPERIMENT_ACLS:
        context = dict(
            experiments=Experiment.objects.prefetch_related("projects").filter(
                projects__id=project_id
            )
        )
    else:
        context = dict(
            experiments=Experiment.safe.all(request.user).filter(
                projects__id=project_id
            )
        )
    return render_response_index(
        request, "ajax/project_latest_experiment.html", context
    )


@never_cache
# @authz.experiment_access_required
def project_recent_experiments(request, project_id):
    if settings.ONLY_EXPERIMENT_ACLS:
        context = dict(
            experiments=Experiment.objects.prefetch_related("projects").filter(
                projects__id=project_id
            )
        )
    else:
        context = dict(
            experiments=Experiment.safe.all(request.user).filter(
                projects__id=project_id
            )
        )
    return render_response_index(
        request, "ajax/experiment_recent_experiments.html", context
    )
