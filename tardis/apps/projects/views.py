"""
views that render full pages
"""

import logging
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.generic.base import TemplateView

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.shortcuts import (
    render_response_index,
    return_response_error,
    return_response_not_found,
)
from tardis.tardis_portal.models import Experiment, Schema
from tardis.tardis_portal.views.utils import _redirect_303
from tardis.tardis_portal.views.pages import _resolve_view
from tardis.tardis_portal.views.parameters import add_par, edit_parameters

from .models import Project, ProjectACL, ProjectParameterSet
from .forms import ProjectForm

logger = logging.getLogger(__name__)


class ProjectView(TemplateView):
    template_name = "view_project.html"

    # TODO: Can me make this a generic function like site_routed_view
    #       that will take an Experiment, Dataset or DataFile and
    #       the associated routing list from settings ?
    # eg
    # schema_routed_view(request, model_instance,
    #                    view_override_tuples, **kwargs)
    def find_custom_view_override(self, request, project):
        """
        Determines if any custom view overrides have been defined in
        settings.PROJECT_VIEWS and returns the view function if a match
        to one the schemas for the project is found.
        (PROJECT_VIEWS is a list of (schema_namespace, view_function) tuples).
        :param request:
        :type request:
        :param project:
        :type project:
        :return:
        :rtype:
        """
        if hasattr(settings, "PROJECT_VIEWS"):
            namespaces = [ps.schema.namespace for ps in project.getParameterSets()]
            for ns, view_fn in settings.PROJECT_VIEWS:
                ns_match = next((n for n in namespaces if re.match(ns, n)), None)
                if ns_match:
                    try:
                        fn = _resolve_view(view_fn)
                        return fn(request, project_id=project.id)
                    except (ImportError, AttributeError) as e:
                        logger.error(
                            "custom view import failed. view name: %s, "
                            "error-msg: %s" % (repr(view_fn), e)
                        )
                        if settings.DEBUG:
                            raise e
        return None

    def get_context_data(self, request, project, **kwargs):
        """
        Prepares the values to be passed to the default dataset view,
        respecting authorization rules. Returns a dict of values (the context).
        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param project: the Project model instance
        :type project: tardis.tardis_portal.models.project.Project
        :param dict kwargs:
        :return: A dictionary of values for the view/template.
        :rtype: dict
        """

        # This might need to be more complex to account for users
        c = super().get_context_data(**kwargs)

        if request.user.is_authenticated:
            is_owner = authz.has_ownership(request, project.id, "project")
        else:
            is_owner = None

        c.update(
            {
                "project": project,
                "has_write_permissions": authz.has_write(
                    request, project.id, "project"
                ),
                "has_download_permissions": authz.has_download_access(
                    request, project.id, "project"
                ),
                "has_sensitive_permissions": authz.has_sensitive_access(
                    request, project.id, "project"
                ),
                "is_owner": is_owner,
                "parametersets": project.projectparameterset_set.exclude(
                    schema__hidden=True
                ),
            }
        )

        # _add_protocols_and_organizations(request, project, c)
        return c

    def get(self, request, *args, **kwargs):
        """
        View an existing project.
        This default view can be overriden by defining a dictionary
        PROJECT_VIEWS in settings.
        :param request: a HTTP request object
        :type request: :class:`django.http.HttpRequest`
        :param list args:
        :param dict kwargs:
        :return: The Django response object
        :rtype: :class:`django.http.HttpResponse`
        """
        project_id = kwargs.get("project_id", None)
        if project_id is None:
            return return_response_error(request)
        try:
            if not authz.has_access(request, project_id, "project"):
                return return_response_error(request)
            project = Project.objects.get(id=project_id)
        except PermissionDenied:
            return return_response_error(request)
        except Project.DoesNotExist:
            return return_response_not_found(request)
        view_override = self.find_custom_view_override(request, project)
        if view_override is not None:
            return view_override
        c = self.get_context_data(request, project, **kwargs)
        template_name = kwargs.get("template_name", None)
        if template_name is None:
            template_name = self.template_name
        return render_response_index(request, template_name, c)


@permission_required("tardis_portal.add_project")
@login_required
def create_project(request):
    c = {
        "subtitle": "Create Project",
        "user_id": request.user.id,
    }

    # Process form or prepopulate it
    if request.method == "POST":
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = Project(created_by=request.user)
            experiments = form.cleaned_data.get("experiments")
            if settings.ONLY_EXPERIMENT_ACLS and not experiments:
                c["status"] = "Please specify one or more experiments."
            else:
                project.name = form.cleaned_data["name"]
                project.description = form.cleaned_data["description"]
                project.principal_investigator = form.cleaned_data[
                    "principal_investigator"
                ]
                project.save()
                institutions = form.cleaned_data.get("institution")
                project.institution.add(*institutions)
                project.experiments.add(*experiments)
                project.save()
                # add default ACL
                acl = ProjectACL(
                    project=project,
                    user=request.user,
                    canRead=True,
                    canDownload=True,
                    canWrite=True,
                    canDelete=True,
                    canSensitive=True,
                    isOwner=True,
                    aclOwnershipType=ProjectACL.OWNER_OWNED,
                )
                acl.save()
                if request.user.id != project.principal_investigator.id:
                    # add default ACL
                    acl = ProjectACL(
                        project=project,
                        user=project.principal_investigator,
                        canRead=True,
                        canDownload=True,
                        canWrite=True,
                        canDelete=True,
                        canSensitive=True,
                        isOwner=True,
                        aclOwnershipType=ProjectACL.OWNER_OWNED,
                    )
                    acl.save()

                request.POST = {"status": "Project Created."}
                return _redirect_303("tardis.apps.projects.view_project", project.id)

        if c["status"] != "Please specify one or more experiments.":
            c["status"] = "Errors exist in form."
        c["error"] = "true"
    else:
        form = ProjectForm(user=request.user)
    c["form"] = form

    return render_response_index(request, "create_project.html", c)


@login_required
@permission_required("tardis_portal.change_project")
@authz.project_write_permissions_required
def edit_project(request, project_id):
    project = Project.objects.get(id=project_id)

    c = {
        "subtitle": "Edit Project",
        "project_id": project_id,
    }

    # Process form or prepopulate it
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                project.name = form.cleaned_data["name"]
                project.description = form.cleaned_data["description"]
                existing_inst = project.institutions.all()
                for inst in form.cleaned_data["institution"]:
                    project.institution.add(inst)
                project.experiments.clear()
                for exp in form.cleaned_data["experiments"]:
                    project.experiments.add(exp)
                project.save()
            return _redirect_303("tardis.apps.projects.view_project", project.id)
        c["status"] = "Errors exist in form."
        c["error"] = "true"
    else:
        form = ProjectForm(instance=project, user=request.user)

    c = {"form": form, "project": project}
    return render_response_index(request, "create_project.html", c)


@login_required
def my_projects(request):
    """
    show owned_and_shared data with credential-based access
    """

    if settings.ONLY_EXPERIMENT_ACLS:
        owned_projects = Project.objects.filter(
            experiments__in=Experiment.safe.owned_and_shared(user=request.user)
        ).order_by("-start_time")
    else:
        owned_projects = Project.safe.owned_and_shared(user=request.user).order_by(
            "-start_time"
        )
    proj_expand_accordion = getattr(settings, "EXPS_EXPAND_ACCORDION", 5)
    c = {
        "owned_projects": owned_projects,
        "proj_expand_accordion": proj_expand_accordion,
    }
    return render_response_index(request, "my_projects.html", c)


def public_projects(request):
    """
    list of public projects
    """

    if settings.ONLY_EXPERIMENT_ACLS:
        public_projects = Project.objects.filter(
            experiments__in=Experiment.safe.public()
        ).order_by("-start_time")
    else:
        public_projects = Project.safe.public().order_by("-start_time")

    c = {"public_projects": public_projects}
    return render_response_index(request, "public_projects.html", c)


@never_cache
@login_required
def retrieve_owned_proj_list(request, template_name="ajax/proj_list.html"):
    projects = []

    if "tardis.apps.projects" in settings.INSTALLED_APPS:
        from tardis.apps.projects.models import Project

    if settings.ONLY_EXPERIMENT_ACLS:
        projects = Project.objects.filter(
            experiments__in=Experiment.safe.owned_and_shared(user=request.user)
        ).order_by("-start_time")
    else:
        projects = Project.safe.owned_and_shared(user=request.user).order_by(
            "-start_time"
        )
    try:
        page_num = int(request.GET.get("page", "0"))
    except ValueError:
        page_num = 0

    paginator = Paginator(projects, settings.OWNED_EXPS_PER_PAGE)
    proj_page = paginator.page(page_num + 1)

    query_string = "/project/ajax/owned_proj_list/?page={page}"

    c = {
        "projects": proj_page,
        "paginator": paginator,
        "page_num": page_num,
        "query_string": query_string,
    }
    return render_response_index(request, template_name, c)


@login_required
def add_project_par(request, project_id):
    parentObject = Project.objects.get(id=project_id)
    if authz.has_write(request, parentObject.id, "project"):
        return add_par(request, parentObject, otype="project", stype=Schema.PROJECT)
    return return_response_error(request)


@login_required
def edit_project_par(request, parameterset_id):
    parameterset = ProjectParameterSet.objects.get(id=parameterset_id)
    if authz.has_write(request, parameterset.project.id, "project"):
        view_sensitive = authz.has_sensitive_access(
            request, parameterset.project.id, "project"
        )
        return edit_parameters(
            request, parameterset, otype="project", view_sensitive=view_sensitive
        )
    return return_response_error(request)
