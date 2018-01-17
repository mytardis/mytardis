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
        if not user.is_authenticated():
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
        if not user.is_authenticated():
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
        if not user.is_authenticated():
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
