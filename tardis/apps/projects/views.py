"""
views that render full pages
"""

import logging
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.views.generic.base import TemplateView

from tardis.tardis_portal.shortcuts import (
    render_response_index,
    return_response_error,
    return_response_not_found,
)
from tardis.tardis_portal.views.utils import _redirect_303

from .models import Project, ProjectACL
from .forms import ProjectForm

logger = logging.getLogger(__name__)


class ProjectView(TemplateView):
    template_name = "tardis_portal/view_project.html"
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
        c["subtitle"] = project.name
        c["project"] = project
        c.update(
            {
                "project": project,
                "subtitle": project.name,
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
            project = Project.safe.get(request.user, project_id)
        except PermissionDenied:
            return return_response_error(request)
        except Project.DoesNotExist:
            return return_response_not_found(request)
        view_override = self.find_custom_view_override(request, project)
        if view_override is not None:
            return view_override
        c = self.get_context_data(request, Project, **kwargs)
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
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = Project()
            project.name = form.cleaned_data["name"]
            project.raid = form.cleaned_data["raid"]
            project.description = form.cleaned_data["description"]
            project.owner = form.cleaned_data["owner"]
            project.save()
            contacts = form.cleaned_data.get("contact")
            project.contact.add(*contacts)
            members = form.cleaned_data.get("member")
            project.member.add(*members)
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

            return _redirect_303("tardis_portal.create_project", project.id)
    else:
        form = ProjectForm()

    c = {"form": form}
    return render_response_index(request, "tardis_portal/create_project.html", c)


@login_required
def edit_project(request, project_id):

    project = Project.objects.get(id=project_id)

    # Process form or prepopulate it
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = Project()
            project.name = form.cleaned_data["name"]
            project.raid = form.cleaned_data["raid"]
            project.description = form.cleaned_data["description"]
            project.owner = form.cleaned_data["owner"]
            project.contact = form.cleaned_data["contact"]
            project.member = form.cleaned_data["member"]
            project.save()
            return _redirect_303("tardis_portal.view_project", project.id)
    else:
        form = ProjectForm(instance=project)

    c = {"form": form, "project": project}
    return render_response_index(request, "tardis_portal/create_project.html", c)
