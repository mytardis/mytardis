from django.apps import apps
from django.conf import settings

from tardis.tardis_portal.managers import ExperimentManager


class PublicationManager(ExperimentManager):
    """
    Extends the ExperimentManager class, added methods for
    draft, scheduled and published publications.
    """
    def draft_publications(self, user):
        """
        Return all draft publications which are owned by a particular user,
        including those shared with a group of which the user is a member.

        :param user: the user who we are retrieving draft publications for
        :type user: django.contrib.auth.models.User

        :returns: A QuerySet of experiments representing the draft publications
        :rtype: QuerySet
        """
        from tardis.tardis_portal.models import Experiment

        # the user must be authenticated
        if not user.is_authenticated:
            return self.get_queryset().none()

        query = self._query_owned(user)
        for group in user.groups.all():
            query |= self._query_owned_by_group(group)
        exps = self.get_queryset().filter(query)
        Schema = apps.get_model('tardis_portal', 'Schema')
        ExperimentParameterSet = apps.get_model('tardis_portal',
                                                'ExperimentParameterSet')
        publication_schema_root = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              Experiment.PUBLICATION_SCHEMA_ROOT))
        exp_psets = ExperimentParameterSet.objects.filter(
            experiment__in=exps, schema=publication_schema_root)
        draft_pub_exp_ids = \
            [exp_pset.experiment.id for exp_pset in exp_psets
             if exp_pset.experiment.is_publication_draft()]
        return exps.filter(id__in=draft_pub_exp_ids).distinct()

    def scheduled_publications(self, user):
        """
        Return all scheduled publications which are owned by a particular user,
        including those shared with a group of which the user is a member.

        :param user: the user who we are retrieving draft publications for
        :type user: django.contrib.auth.models.User

        :returns: A QuerySet of experiments representing the draft publications
        :rtype: QuerySet
        """
        from tardis.tardis_portal.models import Experiment

        # the user must be authenticated
        if not user.is_authenticated:
            return self.get_queryset().none()

        query = self._query_owned(user)
        for group in user.groups.all():
            query |= self._query_owned_by_group(group)
        exps = self.get_queryset().filter(query)
        Schema = apps.get_model('tardis_portal', 'Schema')
        ExperimentParameterSet = apps.get_model('tardis_portal',
                                                'ExperimentParameterSet')
        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              Experiment.PUBLICATION_SCHEMA_ROOT))
        exp_psets = ExperimentParameterSet.objects.filter(
            experiment__in=exps, schema=publication_root_schema)
        scheduled_pub_exp_ids = \
            [exp_pset.experiment.id for exp_pset in exp_psets
             if exp_pset.experiment.public_access == Experiment.PUBLIC_ACCESS_EMBARGO]
        return exps.filter(id__in=scheduled_pub_exp_ids).distinct()

    def released_publications(self, user):
        """
        Return all released publications which are owned by a particular user,
        including those shared with a group of which the user is a member.

        :param user: the user who we are retrieving draft publications for
        :type user: django.contrib.auth.models.User

        :returns: A QuerySet of experiments representing the draft publications
        :rtype: QuerySet
        """
        from tardis.tardis_portal.models import Experiment

        # the user must be authenticated
        if not user.is_authenticated:
            return self.get_queryset().none()

        query = self._query_owned(user)
        for group in user.groups.all():
            query |= self._query_owned_by_group(group)
        exps = self.get_queryset().filter(query)
        Schema = apps.get_model('tardis_portal', 'Schema')
        ExperimentParameterSet = apps.get_model('tardis_portal',
                                                'ExperimentParameterSet')
        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              Experiment.PUBLICATION_SCHEMA_ROOT))
        exp_psets = ExperimentParameterSet.objects.filter(
            experiment__in=exps, schema=publication_root_schema)
        released_pub_exp_ids = \
            [exp_pset.experiment.id for exp_pset in exp_psets
             if exp_pset.experiment.public_access == Experiment.PUBLIC_ACCESS_FULL]
        return exps.filter(id__in=released_pub_exp_ids).distinct()

    def retracted_publications(self, user):
        """
        Return all retracted publications which are owned by a particular user,
        including those shared with a group of which the user is a member.

        :param user: the user who we are retrieving retracted publications for
        :type user: django.contrib.auth.models.User

        :returns: A QuerySet of experiments representing the retracted publications
        :rtype: QuerySet
        """
        from tardis.tardis_portal.models import Experiment

        # the user must be authenticated
        if not user.is_authenticated:
            return self.get_queryset().none()

        query = self._query_owned(user)
        for group in user.groups.all():
            query |= self._query_owned_by_group(group)
        exps = self.get_queryset().filter(query)
        Schema = apps.get_model('tardis_portal', 'Schema')
        ExperimentParameterSet = apps.get_model('tardis_portal',
                                                'ExperimentParameterSet')
        publication_schema_root = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              Experiment.PUBLICATION_SCHEMA_ROOT))
        exp_psets = ExperimentParameterSet.objects.filter(
            experiment__in=exps, schema=publication_schema_root)
        retracted_pub_exp_ids = \
            [exp_pset.experiment.id for exp_pset in exp_psets
             if exp_pset.experiment.is_retracted_publication()]
        return exps.filter(id__in=retracted_pub_exp_ids).distinct()

    def create_draft_publication(self, user, publication_title, publication_description):
        """
        Create a new draft publication
        """
        from django.contrib.auth.models import Group

        from tardis.tardis_portal.models.access_control import ObjectACL
        from tardis.tardis_portal.models.parameters import (
            Schema, ExperimentParameterSet, ExperimentParameter, ParameterName)
        from tardis.tardis_portal.auth.localdb_auth import (
            django_user, django_group)

        from .models import Publication
        from . import default_settings

        publication = Publication(created_by=user,
                                  title=publication_title,
                                  description=publication_description)
        publication.save()

        ObjectACL(content_object=publication,
                  pluginId=django_user,
                  entityId=str(user.id),
                  canRead=True,
                  canWrite=False,
                  canDelete=False,
                  isOwner=True,
                  aclOwnershipType=ObjectACL.OWNER_OWNED).save()

        ObjectACL(content_object=publication,
                  pluginId=django_group,
                  entityId=str(
                      Group.objects.get(
                          name=getattr(
                              settings, 'PUBLICATION_ADMIN_GROUP',
                              default_settings.PUBLICATION_ADMIN_GROUP)).id),
                  canRead=True,
                  canWrite=True,
                  canDelete=True,
                  isOwner=True,
                  aclOwnershipType=ObjectACL.OWNER_OWNED).save()

        publication_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))

        # Attach draft schema
        draft_publication_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                              default_settings.PUBLICATION_DRAFT_SCHEMA))
        ExperimentParameterSet(schema=draft_publication_schema,
                               experiment=publication).save()

        # Attach root schema and blank form_state parameter
        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        publication_root_parameter_set = ExperimentParameterSet(
            schema=publication_schema,
            experiment=publication)
        publication_root_parameter_set.save()
        form_state_param_name = ParameterName.objects.get(
            schema=publication_root_schema, name='form_state')
        ExperimentParameter(name=form_state_param_name,
                            parameterset=publication_root_parameter_set).save()

        return publication
