import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Prefetch
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils.timezone import now as django_time_now

# from X.models import DataManagementPlan # Hook in place for future proofing
from tardis.tardis_portal.managers import OracleSafeManager, SafeManager
from tardis.tardis_portal.models.access_control import ACL, delete_if_all_false

# from tardis.tardis_portal.models.institution import Institution
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import Parameter, ParameterSet

logger = logging.getLogger(__name__)


PROJECT_INSTITUTION = "projects.DefaultInstitutionProfile"

# IMPLEMENT ONCE INSTRUMENT_PROFILE APP IS CREATED, NOT BEFORE
# if "tardis.apps.institution_profile" in settings.INSTALLED_APPS:
#    from tardis.apps.institution_profile import InstitutionProfile - not sure if this code is needed
#    PROJECT_INSTITUTION = InstitutionProfile


class DefaultInstitutionProfile(models.Model):

    name = models.CharField(
        max_length=255, null=False, blank=False, default=settings.DEFAULT_INSTITUTION
    )

    def __str__(self):
        return self.name


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
    # pid = models.CharField(max_length=255, null=False, blank=False, unique=True)
    description = models.TextField()
    locked = models.BooleanField(default=False)
    public_access = models.PositiveSmallIntegerField(
        choices=PUBLIC_ACCESS_CHOICES, null=False, default=PUBLIC_ACCESS_NONE
    )
    principal_investigator = models.ForeignKey(
        User, related_name="principal_investigator", on_delete=models.CASCADE
    )
    institution = models.ManyToManyField(
        PROJECT_INSTITUTION, related_name="institutions"
    )
    embargo_until = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(default=django_time_now)
    end_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(max_length=255, null=True, blank=True)
    experiments = models.ManyToManyField(
        Experiment, related_name="projects", blank=True
    )
    objects = OracleSafeManager()
    safe = SafeManager()

    # TODO Integrate DMPs into the project.
    # data_management_plan = models.ManyToManyField(DataManagementPlan,
    #                                              null=True, blank=True)

    class Meta:
        app_label = "projects"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def getParameterSets(self):
        """Return the project parametersets associated with this
        project.
        """
        from tardis.tardis_portal.models.parameters import Schema

        return self.projectparameterset_set.filter(schema__type=Schema.PROJECT)

    def is_embargoed(self):
        if self.embargo_until:
            if datetime.now() < self.embargo_until:
                return True
        return False

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the absolute url to the current ``Project``"""
        return reverse(
            "tardis.apps.projects.view_project", kwargs={"project_id": self.id}
        )

    def get_edit_url(self):
        """Return the absolute url to the edit view of the current
        ``Project``
        """
        return reverse(
            "tardis.apps.projects.edit_project", kwargs={"project_id": self.id}
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

    def get_groups(self):
        acls = self.projectacl_set.select_related("group").filter(group__isnull=False)
        return [acl.get_related_object() for acl in acls]

    def public_download_allowed(self):
        """
        instance method version of 'public_access_implies_distribution'
        """
        return self.public_access > Project.PUBLIC_ACCESS_METADATA

    def _has_any_perm(self, user_obj):
        if not hasattr(self, "id"):
            return False
        return self.experiments.all()

    def _has_view_perm(self, user_obj):
        if not settings.ONLY_EXPERIMENT_ACLS:
            if self.public_access >= self.PUBLIC_ACCESS_METADATA:
                return True
        return self._has_any_perm(user_obj)

    def _has_download_perm(self, user_obj):
        if not settings.ONLY_EXPERIMENT_ACLS:
            if self.public_download_allowed():
                return True
        return self._has_any_perm(user_obj)

    def _has_change_perm(self, user_obj):
        if self.locked:
            return False
        return self._has_any_perm(user_obj)

    def _has_sensitive_perm(self, user_obj):
        return self._has_any_perm(user_obj)

    def _has_delete_perm(self, user_obj):
        if self.locked:
            return False
        return self._has_any_perm(user_obj)

    def get_datafiles(self, user):
        from tardis.tardis_portal.models.datafile import DataFile

        if settings.ONLY_EXPERIMENT_ACLS:
            return (
                DataFile.objects.select_related("dataset")
                .prefetch_related(
                    Prefetch(
                        "dataset__experiments",
                        queryset=Experiment.safe.all(request.user),
                    )
                )
                .filter(dataset__experiments__projects=self)
            )
        return DataFile.safe.all(user).filter(dataset__experiments__projects=self)

    def get_datasets(self, user):
        from tardis.tardis_portal.models.dataset import Dataset

        if settings.ONLY_EXPERIMENT_ACLS:
            return Dataset.objects.prefetch_related(
                Prefetch("experiments", queryset=Experiment.safe.all(request.user))
            ).filter(experiments__projects=self)
        return Dataset.safe.all(user).filter(experiments__projects=self)

    def get_size(self, user, downloadable=False):
        from tardis.tardis_portal.models.datafile import DataFile

        return DataFile.sum_sizes(self.get_datafiles(user))


class ProjectParameter(Parameter):
    parameterset = models.ForeignKey("ProjectParameterSet", on_delete=models.CASCADE)
    parameter_type = "Project"

    class Meta:
        app_label = "projects"


class ProjectParameterSet(ParameterSet):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    parameter_class = ProjectParameter

    class Meta:
        app_label = "projects"

    def _get_label(self):
        return ("project.name", "Project")


class ProjectACL(ACL):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        app_label = "projects"

    def __str__(self):
        return str(self.id)


def project_public_acls(instance, **kwargs):
    # Post save function to create/delete ACLs for the PUBLIC_USER based upon
    # project public_access flag
    PUBLIC_USER = User.objects.get(pk=settings.PUBLIC_USER_ID)
    if instance.public_access > 25:  # 25 = Embargoed
        if not settings.ONLY_EXPERIMENT_ACLS:
            if isinstance(instance, Project):
                if (
                    not PUBLIC_USER.projectacls.select_related("project")
                    .filter(project__id=instance.id)
                    .exists()
                ):
                    acl = ProjectACL(
                        user=PUBLIC_USER,
                        project=instance,
                        canRead=True,
                        aclOwnershipType=ProjectACL.SYSTEM_OWNED,
                    )
                    acl.save()
    else:
        if isinstance(instance, Project):
            PUBLIC_USER.projectacls.select_related("project").filter(
                project__id=instance.id
            ).delete()


post_save.connect(delete_if_all_false, sender=ProjectACL)

post_save.connect(project_public_acls, sender=Project)
