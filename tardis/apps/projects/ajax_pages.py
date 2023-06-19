from django.conf import settings
from django.views.decorators.cache import never_cache

import tardis.tardis_portal.auth.decorators as authz
from tardis.tardis_portal.models import Experiment
from tardis.tardis_portal.shortcuts import render_response_index

from .models import Project


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
            experiments=Experiment.safe.all(user=request.user).filter(
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
            experiments=Experiment.safe.all(user=request.user).filter(
                projects__id=project_id
            )
        )
    return render_response_index(
        request, "ajax/project_recent_experiments.html", context
    )


@authz.project_access_required
def retrieve_project_metadata(request, project_id):
    project = Project.objects.get(pk=project_id)
    has_write_permissions = authz.has_write(request, project_id, "project")
    has_sensitive_permissions = authz.has_sensitive_access(
        request, project_id, "project"
    )
    parametersets = project.projectparameterset_set.exclude(schema__hidden=True)

    c = {
        "project": project,
        "parametersets": parametersets,
        "has_write_permissions": has_write_permissions,
        "has_sensitive_permissions": has_sensitive_permissions,
    }

    return render_response_index(request, "ajax/project_metadata.html", c)
