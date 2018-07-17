from django.conf import settings
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from tardis.tardis_portal.models import (
    Experiment,
    ExperimentAuthor,
    Schema,
    ParameterName,
    ExperimentParameter,
    ExperimentParameterSet)

from . import default_settings


@python_2_unicode_compatible
class Publication(Experiment):
    """
    Publication records are just experiment records with some metadata, so they
    can be represented by the Experiment model.  However, it is useful to have
    a publication-specific manager, so we can retrieve publication records with
    Publication.safe.draft_publications(user)
    """
    from .managers import PublicationManager

    safe = PublicationManager()  # The acl-aware specific manager.

    class Meta:
        # Don't create a database table for this model:
        proxy = True
        auto_created = True

    def __str__(self):
        return self.title

    def add_root_schema_pset(self):
        pub_schema_root = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        try:
            pub_schema_root_parameter_set = ExperimentParameterSet.objects.get(
                    experiment=self,
                    schema=pub_schema_root)
        except ExperimentParameterSet.DoesNotExist:
            pub_schema_root_parameter_set = ExperimentParameterSet(
                schema=pub_schema_root,
                experiment=self)
            pub_schema_root_parameter_set.save()
        return pub_schema_root_parameter_set

    def get_form_state_parameter(self):
        '''
        Get the form state database object
        '''
        return ExperimentParameter.objects.get(
            name__name='form_state',
            name__schema__namespace=getattr(
                settings, 'PUBLICATION_SCHEMA_ROOT',
                default_settings.PUBLICATION_SCHEMA_ROOT),
            parameterset__experiment=self)

    @staticmethod
    def get_details_schema():
        '''
        Get the publication details schema
        '''
        return Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_DETAILS_SCHEMA',
                              default_settings.PUBLICATION_DETAILS_SCHEMA))

    def get_details_schema_pset(self):
        '''
        Get the publication details schema parameter set
        '''
        return ExperimentParameterSet.objects.get(
            schema=self.get_details_schema(), experiment=self)

    def add_details_schema_pset(self):
        '''
        Attach the publication details schema
        '''
        pub_details_schema = Publication.get_details_schema()
        try:
            pub_details_parameter_set = self.get_details_schema_pset()
        except ExperimentParameterSet.DoesNotExist:
            pub_details_parameter_set = ExperimentParameterSet(
                schema=pub_details_schema,
                experiment=self)
            pub_details_parameter_set.save()
        return pub_details_parameter_set

    def add_acknowledgements(self, acknowledgements):
        '''
        Add the acknowledgements
        '''
        pub_details_schema = Publication.get_details_schema()
        pub_details_parameter_set = self.get_details_schema_pset()
        acknowledgements_parameter_name = ParameterName.objects.get(
            schema=pub_details_schema,
            name='acknowledgements')
        try:
            acknowledgements_param = ExperimentParameter.objects.get(
                name=acknowledgements_parameter_name,
                parameterset=pub_details_parameter_set)
            acknowledgements_param.string_value = acknowledgements
            acknowledgements_param.save()
        except ExperimentParameter.DoesNotExist:
            ExperimentParameter.objects.create(
                name=acknowledgements_parameter_name,
                parameterset=pub_details_parameter_set,
                string_value=acknowledgements)

    def remove_draft_status(self):
        ExperimentParameterSet.objects.get(
            schema__namespace=getattr(
                settings, 'PUBLICATION_DRAFT_SCHEMA',
                default_settings.PUBLICATION_DRAFT_SCHEMA),
            experiment=self).delete()

    def set_embargo_release_date(self, release_date):
        pub_schema_root = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        try:
            pub_schema_root_parameter_set = ExperimentParameterSet.objects.get(
                    experiment=self,
                    schema=pub_schema_root)
        except ExperimentParameterSet.DoesNotExist:
            pub_schema_root_parameter_set = self.add_root_schema_pset()
        embargo_parameter_name = ParameterName.objects.get(
            schema=pub_schema_root,
            name='embargo')
        try:
            param = ExperimentParameter.objects.get(
                name=embargo_parameter_name,
                parameterset=pub_schema_root_parameter_set)
            param.datetime_value = release_date
            param.save()
        except ExperimentParameter.DoesNotExist:
            ExperimentParameter(name=embargo_parameter_name,
                                parameterset=pub_schema_root_parameter_set,
                                datetime_value=release_date).save()

    def revert_to_draft(self, message=None):
        '''
        This method is not currently exposed to users.

        In a previous version of the publication workflow, this method was used
        when proposed publications were rejected by the publication admins.

        Anything with the form_state parameter can be reverted to draft
        '''
        from .utils import send_mail_to_authors
        from .email_text import email_pub_reverted_to_draft

        try:
            # Check that the publication is currently finalised but not released
            if self.is_publication_draft() and self.is_publication() \
                    and self.public_access == Experiment.PUBLIC_ACCESS_NONE:  # pylint: disable=E0203
                return False

            # Check that form_state exists (raises an exception if not)
            schema_ns_root = getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                                     default_settings.PUBLICATION_SCHEMA_ROOT)
            ExperimentParameter.objects.get(
                name__name='form_state',
                name__schema__namespace=schema_ns_root,
                parameterset__experiment=self)

            # Reduce access level to none
            self.public_access = Experiment.PUBLIC_ACCESS_NONE
            self.save()

            # Add the draft schema
            draft_schema_ns = getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                                      default_settings.PUBLICATION_DRAFT_SCHEMA)
            draft_publication_schema = Schema.objects.get(
                namespace=draft_schema_ns)
            ExperimentParameterSet(schema=draft_publication_schema,
                                   experiment=self).save()

            # Delete all metadata except for the form_state
            # Clear any current parameter sets except for those belonging
            # to the publication draft schema or containing the form_state
            # parameter
            for parameter_set in self.getParameterSets():
                if parameter_set.schema.namespace != draft_schema_ns and \
                                parameter_set.schema.namespace != schema_ns_root:
                    parameter_set.delete()
                elif parameter_set.schema.namespace == schema_ns_root:
                    try:
                        ExperimentParameter.objects.get(
                            name__name='form_state',
                            name__schema__namespace=schema_ns_root,
                            parameterset=parameter_set)
                    except ExperimentParameter.DoesNotExist:
                        parameter_set.delete()

            # Send notification emails -- must be done before authors are deleted
            subject, email_message = email_pub_reverted_to_draft(
                self.title, message)

            send_mail_to_authors(self, subject, email_message)

            # Delete all author records
            ExperimentAuthor.objects.filter(experiment=self).delete()

            return True

        except ExperimentParameter.DoesNotExist:
            return False

    def retract(self):
        '''
        Retract a publication
        '''
        from .utils import send_mail_to_authors
        from .email_text import email_pub_retracted

        # Reduce access level to none
        # FIXME: Maybe better to display to message saying why it was retracted
        self.public_access = Experiment.PUBLIC_ACCESS_NONE
        self.save()

        # Add the retracted schema
        retracted_schema_ns = getattr(
            settings, 'PUBLICATION_RETRACTED_SCHEMA',
            default_settings.PUBLICATION_RETRACTED_SCHEMA)
        retracted_publication_schema = Schema.objects.get(
            namespace=retracted_schema_ns)
        retracted_pset = ExperimentParameterSet.objects.create(
            schema=retracted_publication_schema, experiment=self)

        retracted_parameter_name = ParameterName.objects.get(
            schema=retracted_publication_schema,
            name='retracted')
        retracted_param = ExperimentParameter.objects.create(
            name=retracted_parameter_name,
            parameterset=retracted_pset)
        retracted_param.datetime_value = timezone.now()
        retracted_param.save()

        # Send notification emails
        subject, email_message = email_pub_retracted(self.title)

        send_mail_to_authors(self, subject, email_message)
