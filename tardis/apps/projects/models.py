import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from django.db.models.signals import post_save

from django.utils.timezone import now as django_time_now

from tardis.tardis_portal.models.institution import Institution
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import Parameter, ParameterSet
from tardis.tardis_portal.models.access_control import (
    ACL,
    delete_if_all_false,
    public_acls,
)

# from X.models import DataManagementPlan # Hook in place for future proofing
from tardis.tardis_portal.managers import OracleSafeManager, SafeManager


logger = logging.getLogger(__name__)


class Project(models.Model):
    """A project is a collection of :class: '~tardis.tardis_portal.experiment.Experiment'
    records. A project can have multiple Experiments but an experiment has only one
    Project.
    Inputs:
    =================================
    """

    PUBLIC_ACCESS_NONE = 1
    PUBLIC_ACCESS_EMBARGO = 25
    PUBLIC_ACCESS_METADATA = 50
    PUBLIC_ACCESS_FULL = 100

    PUBLIC_ACCESS_CHOICES = (
        (PUBLIC_ACCESS_NONE, "No public access (hidden)"),
        (PUBLIC_ACCESS_EMBARGO, "Ready to be released pending embargo expiry"),
        (PUBLIC_ACCESS_METADATA, "Public Metadata only (no data file access)"),
        (PUBLIC_ACCESS_FULL, "Public"),
    )
    name = models.CharField(max_length=255, null=False, blank=False)
    raid = models.CharField(max_length=255, null=False, blank=False, unique=True)
    description = models.TextField()
    locked = models.BooleanField(default=False)
    public_access = models.PositiveSmallIntegerField(
        choices=PUBLIC_ACCESS_CHOICES, null=False, default=PUBLIC_ACCESS_NONE
    )
    # TODO No project should have the ingestion service account as the lead_researcher
    lead_researcher = models.ForeignKey(
        User, related_name="lead_researcher", on_delete=models.CASCADE
    )
    embargo_until = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(default=django_time_now)
    end_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(max_length=255, null=True, blank=True)
    institution = models.ManyToManyField(Institution, related_name="projects")
    experiments = models.ManyToManyField(Experiment, related_name="projects")
    objects = OracleSafeManager()
    safe = SafeManager()

    # TODO Integrate DMPs into the project.
    # data_management_plan = models.ManyToManyField(DataManagementPlan,
    #                                              null=True, blank=True)

    class Meta:
        app_label = "tardis_portal"

    def save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)

    def getParameterSets(self):
        """Return the project parametersets associated with this
        project.
        """
        from .parameters import Schema

        return self.projectparameterset_set.filter(schema__schema_type=Schema.PROJECT)

    def getParametersforIndexing(self):
        """Returns the project parameters associated with this
        project, formatted for elasticsearch.
        """
        from .parameters import ProjectParameter, ParameterName

        paramsets = list(self.getParameterSets())
        parameter_groups = {
            "string": [],
            "numerical": [],
            "datetime": [],
            "schemas": [],
        }
        for paramset in paramsets:
            param_type = {1: "datetime", 2: "string", 3: "numerical"}
            param_glob = (
                ProjectParameter.objects.filter(parameterset=paramset)
                .all()
                .values_list(
                    "name",
                    "datetime_value",
                    "string_value",
                    "numerical_value",
                    "sensitive_metadata",
                )
            )
            parameter_groups["schemas"].append({"schema_id": paramset.schema_id})
            for sublist in param_glob:
                PN_id = ParameterName.objects.get(id=sublist[0])
                param_dict = {}
                type_idx = 0
                for idx, value in enumerate(sublist[1:-1]):
                    if value not in [None, ""]:
                        param_dict["pn_id"] = str(PN_id.id)
                        param_dict["pn_name"] = str(PN_id.full_name)
                        if sublist[-1]:
                            param_dict["sensitive"] = True
                        else:
                            param_dict["sensitive"] = False

                        type_idx = idx + 1

                        if type_idx == 1:
                            param_dict["value"] = value
                        elif type_idx == 2:
                            param_dict["value"] = str(value)
                        elif type_idx == 3:
                            param_dict["value"] = float(value)
                parameter_groups[param_type[type_idx]].append(param_dict)
        return parameter_groups

    def getACLsforIndexing(self):
        """Returns the projectACLs associated with this
        project, formatted for elasticsearch.
        """
        return_list = []
        for acl in self.projectacl_set.all():
            acl_dict = {}
            if acl.user is not None:
                acl_dict["pluginId"] = "django_user"
                acl_dict["entityId"] = acl.user.id
                return_list.append(acl_dict)
            if acl.group is not None:
                acl_dict["pluginId"] = "django_group"
                acl_dict["entityId"] = acl.group.id
                return_list.append(acl_dict)
            # if acl.token is not None:
            #    acl_dict["pluginId"] = "token"
            #    acl_dict["entityId"] = acl.token.id
            #    return_list.append(acl_dict)
        return return_list

    def is_embargoed(self):
        if self.embargo_until:
            if datetime.now() < self.embargo_until:
                return True
        return False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute url to the current ``Project``"""
        return reverse("tardis_portal.view_project", kwargs={"project_id": self.id})

    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Project``
        """
        return reverse(
            "tardis.tardis_portal.views.edit_project", kwargs={"project_id": self.id}
        )

    def get_ct(self):
        return ContentType.objects.get_for_model(self)

    def get_owners(self):
        acls = self.projectacl_set.select_related("user").filter(
            user__isnull=False, isOwner=True
        )
        return [acl.get_related_object() for acl in acls]

    def get_users(self):
        acls = self.projectacl_set.select_related("user").filter(
            user__isnull=False, isOwner=False
        )
        return [acl.get_related_object() for acl in acls]

    def get_users_and_perms(self):
        acls = self.projectacl_set.select_related("user").filter(
            user__isnull=False, isOwner=False
        )
        ret_list = []
        if acls.exists():
            for acl in acls:
                user = acl.get_related_object()
                sensitive_flg = acl.canSensitive
                download_flg = acl.canDownload
                ret_list.append([user, sensitive_flg, download_flg])
        return ret_list

    def get_admins(self):
        acls = self.projectacl_set.select_related("group").filter(
            group__isnull=False, isOwner=True
        )
        return [acl.get_related_object() for acl in acls]

    def get_groups(self):
        acls = self.projectacl_set.select_related("group").filter(group__isnull=False)
        return [acl.get_related_object() for acl in acls]

    def get_groups_and_perms(self):
        acls = self.projectacl_set.select_related("group").filter(group__isnull=False)
        ret_list = []
        if acls.exists():
            for acl in acls:
                if not acl.isOwner:
                    group = acl.get_related_object()
                    sensitive_flg = acl.canSensitive
                    download_flg = acl.canDownload
                    ret_list.append([group, sensitive_flg, download_flg])
        return ret_list

    def _has_view_perm(self, user_obj):
        """
        Called from the ACLAwareBackend class's has_perm method
        in tardis/tardis_portal/auth/authorisation.py
        Returning None means we won't override permissions here,
        i.e. we'll leave it to ACLAwareBackend's has_perm method
        to determine permissions from ProjectACLs
        """
        if not hasattr(self, "id"):
            return False
        # May be redundant - left in for the short term
        if self.public_access >= self.PUBLIC_ACCESS_METADATA:
            return True
        return None

    def _has_change_perm(self, user_obj):
        """
        Called from the ACLAwareBackend class's has_perm method
        in tardis/tardis_portal/auth/authorisation.py
        Returning None means we won't override permissions here,
        i.e. we'll leave it to ACLAwareBackend's has_perm method
        to determine permissions from ProjectACLs
        """
        if not hasattr(self, "id"):
            return False
        if self.locked:
            return False
        return None

    def _has_delete_perm(self, user_obj):
        """
        Called from the ACLAwareBackend class's has_perm method
        in tardis/tardis_portal/auth/authorisation.py
        Returning None means we won't override permissions here,
        i.e. we'll leave it to ACLAwareBackend's has_perm method
        to determine permissions from ProjectACLs
        """
        if not hasattr(self, "id"):
            return False
        return None

    def get_datafiles(self, user, downloadable=False):
        from .datafile import DataFile

        return DataFile.safe.all(user, downloadable=downloadable).filter(
            dataset__experiments__project=self
        )

    def get_size(self, user, downloadable=False):
        from .datafile import DataFile

        return DataFile.sum_sizes(self.get_datafiles(user, downloadable=downloadable))

    def to_search(self):
        from tardis.apps.search.documents import ProjectDocument as ProjectDoc

        metadata = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "institution": self.institution,
            "lead_researcher": self.lead_researcher,
            "acls": self.getACLsforIndexing(),
            "parameters": self.getParametersforIndexing(),
        }
        return ProjectDoc(meta=metadata)


class ProjectParameter(Parameter):
    parameterset = models.ForeignKey("ProjectParameterSet", on_delete=models.CASCADE)
    parameter_type = "Project"


class ProjectParameterSet(ParameterSet):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    parameter_class = ProjectParameter

    def _get_label(self):
        return ("project.name", "Project")


class ProjectACL(ACL):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)


post_save.connect(delete_if_all_false, sender=ProjectACL)

post_save.connect(public_acls, sender=Project)
