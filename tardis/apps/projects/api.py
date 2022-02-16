"""
RESTful API for MyTardis models and data.
Implemented with Tastypie.

.. moduleauthor:: Mike Laverick <mike.laverick@auckland.ac.nz>
.. moduleauthor:: Chris Seal <c.seal@auckland.ac.nz>
"""
from itertools import chain

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash

from tardis.tardis_portal.api import (
    MyTardisAuthentication,
    PrettyJSONSerializer,
    ParameterResource,
    ParameterSetResource,
    UserResource,
    ExperimentResource,
)
from tardis.tardis_portal.auth.decorators import (
    has_access,
    has_sensitive_access,
    has_write,
)
from .models import (
    Project,
    ProjectACL,
    ProjectParameter,
    ProjectParameterSet,
    DefaultInstitutionProfile,
)


if settings.DEBUG:
    default_serializer = PrettyJSONSerializer()
else:
    default_serializer = Serializer()

PROJECT_INSTITUTION_RESOURCE = "tardis.apps.projects.api.DefaultInstitutionProfile"


class ProjectACLAuthorization(Authorization):
    """A Project-specific Authorisation class for Tastypie, rather than bloating
    the existing generic MyTardis-API ACLAuthorization class further. It would be
    good to refactor the generic API ACLAuthorization class to be even more generic:
    reducing verboseness of the class and removing this specific project ACLAuth class.
    """

    def read_list(self, object_list, bundle):  # noqa # too complex
        if bundle.request.user.is_authenticated and bundle.request.user.is_superuser:
            return object_list
        if isinstance(bundle.obj, Project):
            project_ids = [
                proj.id
                for proj in object_list
                if has_access(bundle.request, proj.id, "project")
            ]
            return Project.objects.filter(id__in=project_ids)
        if isinstance(bundle.obj, ProjectParameterSet):
            return [
                pps
                for pps in object_list
                if has_access(bundle.request, pps.project.id, "project")
            ]
        if isinstance(bundle.obj, ProjectParameter):
            pp_list = [
                pp
                for pp in object_list
                if has_access(bundle.request, pp.parameterset.project.id, "project")
            ]
            # Generator to filter sensitive exp_parameters when given an exp id
            def get_set_param(set_par):
                if not set_par.name.sensitive:
                    yield set_par
                elif has_sensitive_access(
                    bundle.request, set_par.parameterset.project.id, "project"
                ):
                    yield set_par

            # Take chained generators and turn them into a set of parameters
            return list(chain(chain.from_iterable(map(get_set_param, pp_list))))

        if isinstance(bundle.obj, ProjectACL):
            query = ProjectACL.objects.none()
            if bundle.request.user.is_authenticated:
                query |= bundle.request.user.projectacls.all()
                for group in bundle.request.user.groups.all():
                    query |= group.projectacls.all()
            return query
        return []

    def read_detail(self, object_list, bundle):  # noqa # too complex
        if bundle.request.user.is_authenticated and bundle.request.user.is_superuser:
            return True
        if isinstance(bundle.obj, Project):
            return has_access(bundle.request, bundle.obj.id, "project")
        if isinstance(bundle.obj, ProjectParameterSet):
            return has_access(bundle.request, bundle.obj.project.id, "project")
        if isinstance(bundle.obj, ProjectParameter):
            if bundle.obj.name.sensitive:
                return has_sensitive_access(
                    bundle.request, bundle.obj.parameterset.project.id, "project"
                )
            return has_access(
                bundle.request, bundle.obj.parameterset.project.id, "project"
            )
        raise NotImplementedError(type(bundle.obj))

    def create_list(self, object_list, bundle):
        raise NotImplementedError(type(bundle.obj))

    def create_detail(self, object_list, bundle):  # noqa # too complex
        if not bundle.request.user.is_authenticated:
            return False
        if bundle.request.user.is_authenticated and bundle.request.user.is_superuser:
            return True

        if isinstance(bundle.obj, Project):
            if not bundle.request.user.has_perm("tardis_portal.change_project"):
                return False
            perm = False
            for exp_uri in bundle.data.get("experiments", []):
                try:
                    this_exp = ExperimentResource.get_via_uri(
                        ExperimentResource(), exp_uri, bundle.request
                    )
                except:
                    return False
                if has_write(bundle.request, this_exp.id, "experiment"):
                    perm = True
                else:
                    return False
            return perm
        if isinstance(bundle.obj, ProjectParameterSet):
            if not bundle.request.user.has_perm("tardis_portal.change_project"):
                return False
            project_uri = bundle.data.get("project", None)
            if project_uri is not None:
                project = ProjectResource.get_via_uri(
                    ProjectResource(), project_uri, bundle.request
                )
                return has_write(bundle.request, project.id, "project")
            if getattr(bundle.obj.project, "id", False):
                return has_write(bundle.request, bundle.obj.project.id, "project")
            return False
        if isinstance(bundle.obj, ProjectParameter):
            return bundle.request.user.has_perm(
                "tardis_portal.change_project"
            ) and has_write(
                bundle.request, bundle.obj.parameterset.project.id, "project"
            )
        if isinstance(bundle.obj, ProjectACL):
            return bundle.request.user.has_perm("tardis_portal.add_projectacl")
        raise NotImplementedError(type(bundle.obj))

    def update_list(self, object_list, bundle):
        raise NotImplementedError(type(bundle.obj))

    def update_detail(self, object_list, bundle):  # noqa # too complex
        """
        Latest TastyPie requires update_detail permissions to be able to create
        objects.  Rather than duplicating code here, we'll just use the same
        authorization rules we use for create_detail.
        """
        return self.create_detail(object_list, bundle)

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")


class ProjectResource(ModelResource):
    """API for Projects
    also creates a default ACL and allows ProjectParameterSets to be read
    and written.
    TODO: catch duplicate schema submissions for parameter sets
    """

    created_by = fields.ForeignKey(UserResource, "created_by")
    parameter_sets = fields.ToManyField(
        "tardis.apps.projects.api.ProjectParameterSetResource",
        "projectparameterset_set",
        related_name="project",
        full=True,
        null=True,
    )
    institution = fields.ToManyField(
        PROJECT_INSTITUTION_RESOURCE, "institutions", null=True, full=True
    )
    principal_investigator = fields.ForeignKey(UserResource, "principal_investigator")

    class Meta:
        authentication = MyTardisAuthentication()
        authorization = ProjectACLAuthorization()
        serializer = default_serializer
        object_class = Project
        queryset = Project.objects.all()
        filtering = {
            "id": ("exact",),
            "name": ("exact",),
            "experiments": ALL_WITH_RELATIONS,
            "url": ("exact",),
            "institution": ALL_WITH_RELATIONS,
        }
        ordering = ["id", "name", "url", "start_time", "end_time"]
        always_return_data = True

    def dehydrate(self, bundle):
        from tardis.tardis_portal.models import Experiment

        project = bundle.obj
        size = project.get_size(bundle.request.user)
        bundle.data["size"] = size
        # Both Macro and Micro ACLs route through ExperimentACLs for this
        project_experiment_count = (
            Experiment.safe.all(bundle.request.user).filter(projects=project).count()
        )
        bundle.data["experiment_count"] = project_experiment_count
        project_dataset_count = project.get_datasets(bundle.request.user).count()
        bundle.data["dataset_count"] = project_dataset_count
        project_datafile_count = project.get_datafiles(bundle.request.user).count()
        bundle.data["datafile_count"] = project_datafile_count
        # admins = project.get_admins()
        # bundle.data["admin_groups"] = [acl.id for acl in admins]
        # members = project.get_groups()
        # bundle.data["member_groups"] = [acl.id for acl in members]
        return bundle

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/project-experiments%s$"
                % (self._meta.resource_name, trailing_slash()),
                self.wrap_view("get_project_experiments"),
                name="api_get_project_experiments",
            ),
        ]

    '''def hydrate_m2m(self, bundle):
        """
        Create experiment-dataset associations first, because they affect
        authorization for adding other related resources, e.g. metadata
        """
        if getattr(bundle.obj, "id", False):
            for exp_uri in bundle.data.get("experiments", []):
                try:
                    exp = ExperimentResource.get_via_uri(
                        ExperimentResource(), exp_uri, bundle.request
                    )
                    bundle.obj.experiments.add(exp)
                except NotFound:
                    pass
        # acls = process_acls(bundle)
        # if acls:
        #    bulk_replace_existing_acls(acls)
        # if "admins" in bundle.data.keys():
        #    bundle.data.pop("admins")
        # if "admin_groups" in bundle.data.keys():
        #    bundle.data.pop("admin_groups")
        # if "members" in bundle.data.keys():
        #    bundle.data.pop("members")
        # if "member_groups" in bundle.data.keys():
        #    bundle.data.pop("member_groups")
        return super().hydrate_m2m(bundle)'''

    def obj_create(self, bundle, **kwargs):
        """Currently not tested for failed db transactions as sqlite does not
        enforce limits.
        """
        user = bundle.request.user
        bundle.data["created_by"] = user
        """if not User.objects.filter(
            username=bundle.data["principal_investigator"]
        ).exists():
            new_user = get_user_from_upi(bundle.data["principal_investigator"])
            if not new_user:
                logger.error("No one found for upi: {member}")
            user = User.objects.create(
                username=new_user["username"],
                first_name=new_user["first_name"],
                last_name=new_user["last_name"],
                email=new_user["email"],
            )
            user.set_password(gen_random_password())
            for permission in settings.DEFAULT_PERMISSIONS:
                user.user_permission.add(Permission.objects.get(codename=permission))
            user.save()
            authentication = UserAuthentication(
                userProfile=user.userprofile,
                username=new_user["username"],
                authenticationMethod=settings.LDAP_METHOD,
            )
            authentication.save()"""
        project_lead = User.objects.get(username=bundle.data["principal_investigator"])
        bundle.data["principal_investigator"] = project_lead
        bundle = super().obj_create(bundle, **kwargs)
        return bundle

    def get_project_experiments(self, request, **kwargs):
        """
        Return a list of experiments related to the project
        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        :param kwargs:
        :return: a list of experiments
        :rtype: JsonResponse: :class: `django.http.JsonResponse`
        """
        from tardis.tardis_portal.models import Experiment

        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)
        project_id = kwargs["pk"]
        if not has_access(request, project_id, "project"):
            return HttpResponseForbidden()

        # Both Macro and Micro ACLs route through ExperimentACLs for this
        exp_list = Experiment.safe.all(request.user).filter(projects=project_id)

        exp_list = {"objects": [*exp_list.values("id", "title")]}
        return JsonResponse(exp_list, status=200, safe=False)


class ProjectACLResource(ModelResource):
    project = fields.ForeignKey(ProjectResource, "project")

    class Meta:
        authentication = MyTardisAuthentication()
        authorization = ProjectACLAuthorization()
        object_class = ProjectACL
        queryset = ProjectACL.objects.select_related("user").exclude(
            user__id=settings.PUBLIC_USER_ID
        )
        filtering = {
            "pluginId": ("exact",),
            "entityId": ("exact",),
        }
        ordering = ["id"]

    def hydrate(self, bundle):
        try:
            project = ProjectResource.get_via_uri(
                ProjectResource(), bundle.data["project"], bundle.request
            )
        except NotFound:
            project = Project.objects.get(namespace=bundle.data["project"])
        bundle.obj.project = project
        del bundle.data["project"]
        return bundle


class ProjectParameterSetResource(ParameterSetResource):
    project = fields.ForeignKey(ProjectResource, "project")
    parameters = fields.ToManyField(
        "tardis.apps.projects.api.ProjectParameterResource",
        "projectparameter_set",
        related_name="parameterset",
        full=True,
        null=True,
    )

    class Meta:
        authentication = MyTardisAuthentication()
        authorization = ProjectACLAuthorization()
        serializer = default_serializer
        object_class = ProjectParameterSet
        queryset = ProjectParameterSet.objects.all()

    def dehydrate_parameters(self, bundle):
        if has_sensitive_access(bundle.request, bundle.obj.project.id, "project"):
            return bundle.data["parameters"]
        return [
            x for x in bundle.data["parameters"] if x.obj.name.sensitive is not True
        ]


class ProjectParameterResource(ParameterResource):
    parameterset = fields.ForeignKey(ProjectParameterSetResource, "parameterset")

    class Meta:
        authentication = MyTardisAuthentication()
        authorization = ProjectACLAuthorization()
        serializer = default_serializer
        object_class = ProjectParameter
        queryset = ProjectParameter.objects.all()


class DefaultInstitutionProfileResource(ModelResource):
    class Meta:
        authentication = MyTardisAuthentication()
        authorization = ProjectACLAuthorization()
        serializer = default_serializer
        object_class = DefaultInstitutionProfile
        queryset = DefaultInstitutionProfile.objects.all()
        filtering = {
            "id": ("exact",),
            "name": ("exact",),
        }
        ordering = ["id", "name"]
        always_return_data = True
