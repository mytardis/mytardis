"""
views that return HTML that is injected into pages
"""
import json
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.forms import model_to_dict
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from ..auth import decorators as authz
from ..forms import RightsForm
from ..models import (
    DataFile,
    DatafileParameterSet,
    Dataset,
    Experiment,
    Schema,
    UserProfile,
)
from ..shortcuts import (
    render_response_index,
    return_response_error,
    return_response_not_found,
)
from ..views.pages import ExperimentView
from ..views.utils import _add_protocols_and_organizations

logger = logging.getLogger(__name__)


@authz.experiment_access_required
def experiment_description(request, experiment_id):
    """View an existing experiment's description. To be loaded via ajax.

    :param request: a HTTP Request instance
    :type request: :class:`django.http.HttpRequest`
    :param experiment_id: the ID of the experiment to be edited
    :type experiment_id: string
    :returns: description of the experiment
    :rtype: :class:`django.http.HttpResponse`
    """
    c = {}

    try:
        experiment = Experiment.safe.get(request.user, experiment_id)
    except PermissionDenied:
        return return_response_error(request)
    except Experiment.DoesNotExist:
        return return_response_not_found(request)

    c["experiment"] = experiment
    c["subtitle"] = experiment.title
    c["nav"] = [
        {"name": "Data", "link": "/experiment/view/"},
        {"name": experiment.title, "link": experiment.get_absolute_url()},
    ]

    c["authors"] = experiment.experimentauthor_set.all()

    if settings.ONLY_EXPERIMENT_ACLS:
        c["datafiles"] = (
            DataFile.objects.select_related("dataset")
            .prefetch_related("dataset__experiments")
            .filter(dataset__experiments__id=experiment_id)
        )
    else:
        c["datafiles"] = DataFile.safe.all(user=request.user).filter(
            dataset__experiments__id=experiment_id
        )

    c["owners"] = experiment.get_owners()

    # calculate the sum of the datafile sizes
    c["size"] = DataFile.sum_sizes(c["datafiles"])

    c["has_download_permissions"] = authz.has_download_access(
        request, experiment_id, "experiment"
    )

    c["has_write_permissions"] = authz.has_write(request, experiment_id, "experiment")

    if request.user.is_authenticated:
        c["is_owner"] = authz.has_ownership(request, experiment_id, "experiment")

    _add_protocols_and_organizations(request, experiment, c)

    if "status" in request.GET:
        c["status"] = request.GET["status"]
    if "error" in request.GET:
        c["error"] = request.GET["error"]

    return render_response_index(
        request, "tardis_portal/ajax/experiment_description.html", c
    )


@never_cache
@authz.experiment_access_required
def experiment_datasets(request, experiment_id):
    return ExperimentView.as_view()(
        request,
        experiment_id=experiment_id,
        template_name="tardis_portal/ajax/experiment_datasets.html",
    )


@never_cache
@authz.experiment_access_required
def experiment_latest_dataset(request, experiment_id):
    if settings.ONLY_EXPERIMENT_ACLS:
        context = {
            "datasets": Dataset.objects.prefetch_related("experiments").filter(
                experiments__id=experiment_id
            )
        }
    else:
        context = {
            "datasets": Dataset.safe.all(user=request.user).filter(
                experiments__id=experiment_id
            )
        }
    return render_response_index(
        request, "tardis_portal/ajax/experiment_latest_dataset.html", context
    )


@never_cache
@authz.experiment_access_required
def experiment_recent_datasets(request, experiment_id):
    if settings.ONLY_EXPERIMENT_ACLS:
        context = {
            "datasets": Dataset.objects.prefetch_related("experiments").filter(
                experiments__id=experiment_id
            )
        }
    else:
        context = {
            "datasets": Dataset.safe.all(user=request.user).filter(
                experiments__id=experiment_id
            )
        }
    return render_response_index(
        request, "tardis_portal/ajax/experiment_recent_datasets.html", context
    )


@never_cache
@authz.experiment_access_required
def experiment_dataset_transfer(request, experiment_id):
    experiments = Experiment.safe.owned(user=request.user)

    def get_json_url_pattern():
        placeholder = "314159"
        return reverse(
            "tardis.tardis_portal.views.experiment_datasets_json", args=[placeholder]
        ).replace(placeholder, "{{experiment_id}}")

    c = {
        "experiments": experiments.exclude(id=experiment_id),
        "url_pattern": get_json_url_pattern(),
    }
    return render_response_index(
        request, "tardis_portal/ajax/experiment_dataset_transfer.html", c
    )


@authz.dataset_access_required
def retrieve_dataset_metadata(request, dataset_id):
    dataset = Dataset.objects.get(pk=dataset_id)
    has_write_permissions = authz.has_write(request, dataset_id, "dataset")
    has_sensitive_permissions = authz.has_sensitive_access(
        request, dataset_id, "dataset"
    )
    parametersets = dataset.datasetparameterset_set.exclude(schema__hidden=True)

    c = {
        "dataset": dataset,
        "parametersets": parametersets,
        "has_write_permissions": has_write_permissions,
        "has_sensitive_permissions": has_sensitive_permissions,
    }

    return render_response_index(request, "tardis_portal/ajax/dataset_metadata.html", c)


@never_cache
@authz.experiment_access_required
def retrieve_experiment_metadata(request, experiment_id):
    experiment = Experiment.objects.get(pk=experiment_id)
    has_write_permissions = authz.has_write(request, experiment_id, "experiment")
    has_sensitive_permissions = authz.has_sensitive_access(
        request, experiment_id, "experiment"
    )
    parametersets = experiment.experimentparameterset_set.exclude(schema__hidden=True)

    c = {
        "experiment": experiment,
        "parametersets": parametersets,
        "has_write_permissions": has_write_permissions,
        "has_sensitive_permissions": has_sensitive_permissions,
    }

    return render_response_index(
        request, "tardis_portal/ajax/experiment_metadata.html", c
    )


# @never_cache
@authz.datafile_access_required
def display_datafile_details(request, datafile_id):
    """
    Displays a box, with a list of interaction options depending on
    the file type given and displays the one with the highest priority
    first.
    Views are set up in settings. Order of list is taken as priority.
    Given URLs are called with the datafile id appended.
    """
    # retrieve valid interactions for file type
    the_file = DataFile.objects.get(id=datafile_id)
    the_schemas = [p.schema.namespace for p in the_file.getParameterSets()]
    default_view = "Datafile Metadata"
    apps = [
        (default_view, "/ajax/parameters"),
    ]
    if hasattr(settings, "DATAFILE_VIEWS"):
        apps += settings.DATAFILE_VIEWS

    views = []
    for ns, url in apps:
        if ns == default_view:
            views.append({"url": "%s/%s/" % (url, datafile_id), "name": default_view})
        elif ns in the_schemas:
            schema = Schema.objects.get(namespace__exact=ns)
            views.append({"url": "%s/%s/" % (url, datafile_id), "name": schema.name})
    context = {
        "datafile_id": datafile_id,
        "views": views,
    }
    return render_response_index(
        request, "tardis_portal/ajax/datafile_details.html", context
    )


@never_cache
@authz.datafile_access_required
def retrieve_parameters(request, datafile_id):
    parametersets = DatafileParameterSet.objects.all()
    parametersets = parametersets.filter(datafile__pk=datafile_id).exclude(
        schema__hidden=True
    )

    datafile = DataFile.objects.get(id=datafile_id)
    dataset_id = datafile.dataset.id
    has_write_permissions = authz.has_write(request, dataset_id, "dataset")

    c = {
        "parametersets": parametersets,
        "datafile": datafile,
        "has_write_permissions": has_write_permissions,
        "has_download_permissions": authz.has_download_access(
            request, dataset_id, "dataset"
        ),
    }

    return render_response_index(request, "tardis_portal/ajax/parameters.html", c)


@never_cache  # too complex # noqa
@authz.dataset_access_required
def retrieve_datafile_list(
    request, dataset_id, template_name="tardis_portal/ajax/datafile_list.html"
):
    from django.template.defaultfilters import filesizeformat

    params = {}

    if settings.ONLY_EXPERIMENT_ACLS:
        dataset_results = DataFile.objects.filter(
            dataset__pk=dataset_id,
        ).order_by("filename")
    else:
        dataset_results = (
            DataFile.safe.all(user=request.user)
            .filter(
                dataset__pk=dataset_id,
            )
            .order_by("filename")
        )

    filename_search = None

    if "filename" in request.GET and request.GET["filename"]:
        filename_search = request.GET["filename"]
        dataset_results = dataset_results.filter(filename__icontains=filename_search)

        params["filename"] = filename_search

    # pagination was removed by someone in the interface but not here.
    # need to fix.
    pgresults = 100

    paginator = Paginator(dataset_results, pgresults)

    try:
        page_num = int(request.GET.get("page", "0"))
    except ValueError:
        page_num = 0

    # If page request (9999) is out of range, deliver last page of results.

    try:
        dataset = paginator.page(page_num + 1)
    except (EmptyPage, InvalidPage):
        dataset = paginator.page(paginator.num_pages)

    is_owner = False
    has_download_permissions = authz.has_download_access(request, dataset_id, "dataset")
    has_write_permissions = False

    if request.user.is_authenticated:
        is_owner = authz.has_ownership(request, dataset_id, "dataset")
        has_write_permissions = authz.has_write(request, dataset_id, "dataset")

    immutable = Dataset.objects.get(id=dataset_id).immutable
    ajax_format = request.GET.get("format", "html")
    if ajax_format == "json":
        try:
            offset = int(request.GET.get("offset", 0))
        except ValueError:
            offset = 0
        try:
            limit = int(request.GET.get("limit", pgresults))
        except ValueError:
            limit = pgresults
        datafile_properties_list = []
        for datafile in dataset[offset : offset + limit]:
            datafile_properties_list.append(
                {
                    "id": datafile.id,
                    "filename": datafile.filename,
                    "verified": datafile.verified,
                    "is_online": datafile.is_online,
                    "view_url": datafile.view_url,
                    "has_image": datafile.has_image,
                    "download_url": datafile.download_url,
                    "recall_url": datafile.recall_url,
                    "formatted_size": filesizeformat(datafile.size),
                    "has_download_permissions": authz.has_download_access(
                        request, datafile.id, "datafile"
                    ),
                    "has_write_permissions": authz.has_write(
                        request, datafile.id, "datafile"
                    ),
                }
            )
        return JsonResponse(
            {
                "datafiles": datafile_properties_list,
                "immutable": immutable,
                "has_download_permissions": has_download_permissions,
                "has_write_permissions": has_write_permissions,
            }
        )

    query_string = "/ajax/datafile_list/" + dataset_id + "?page={page}"
    c = {
        "datafiles": dataset,
        "paginator": paginator,
        "page_num": page_num,
        "immutable": immutable,
        "dataset": Dataset.objects.get(id=dataset_id),
        "filename_search": filename_search,
        "is_owner": is_owner,
        "has_download_permissions": has_download_permissions,
        "has_write_permissions": has_write_permissions,
        "params": urlencode(params),
        "query_string": query_string,
    }
    _add_protocols_and_organizations(request, None, c)
    return render_response_index(request, template_name, c)


@authz.experiment_ownership_required
def choose_rights(request, experiment_id):
    """
    Choose access rights and licence.
    """
    experiment = Experiment.objects.get(id=experiment_id)

    def is_valid_owner(owner):
        if not settings.REQUIRE_VALID_PUBLIC_CONTACTS:
            return True

        userProfile, _ = UserProfile.objects.get_or_create(user=owner)

        return userProfile.isValidPublicContact()

    # Forbid access if no valid owner is available (and show error message)
    perms = [is_valid_owner(owner) for owner in experiment.get_owners()]
    if not any(perms):
        c = {"no_valid_owner": True, "experiment": experiment}
        return render_response_index(
            request, "tardis_portal/ajax/unable_to_choose_rights.html", c, status=403
        )

    # Process form or prepopulate it
    if request.method == "POST":
        data = json.loads(request.body)
        form = RightsForm(data)
        if form.is_valid():
            experiment.public_access = form.cleaned_data["public_access"]
            experiment.license = form.cleaned_data["license"]
            experiment.save()
    else:
        form = RightsForm(
            {
                "public_access": experiment.public_access,
                "license": experiment.license_id,
                "legal_text": getattr(
                    settings, "LEGAL_TEXT", "No Legal Agreement Specified"
                ),
            }
        )

    c = {"form": form.data, "experiment": model_to_dict(experiment)}
    return JsonResponse(form.data, safe=False)
    # return render_response_index(
    #    request, 'tardis_portal/ajax/choose_rights.html', c)


@never_cache
@login_required
def retrieve_owned_exps_list(
    request, template_name="tardis_portal/ajax/exps_list.html"
):
    experiments = Experiment.safe.owned(user=request.user).order_by("-update_time")

    try:
        page_num = int(request.GET.get("page", "0"))
    except ValueError:
        page_num = 0

    paginator = Paginator(experiments, settings.OWNED_EXPS_PER_PAGE)
    exps_page = paginator.page(page_num + 1)

    query_string = "/ajax/owned_exps_list/?page={page}"

    c = {
        "experiments": exps_page,
        "paginator": paginator,
        "page_num": page_num,
        "query_string": query_string,
    }
    return render_response_index(request, template_name, c)


@never_cache
@login_required
def retrieve_shared_exps_list(
    request, template_name="tardis_portal/ajax/exps_list.html"
):
    experiments = Experiment.safe.shared(user=request.user).order_by("-update_time")

    try:
        page_num = int(request.GET.get("page", "0"))
    except ValueError:
        page_num = 0

    paginator = Paginator(experiments, settings.SHARED_EXPS_PER_PAGE)
    exps_page = paginator.page(page_num + 1)

    query_string = "/ajax/shared_exps_list/?page={page}"
    c = {
        "experiments": exps_page,
        "paginator": paginator,
        "page_num": page_num,
        "query_string": query_string,
    }
    return render_response_index(request, template_name, c)
