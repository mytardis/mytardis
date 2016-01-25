from django.db import models
from tardis.tardis_portal.models import Facility


class Instrument(models.Model):
    '''
    Represents an instrument belonging to a facility that produces data
    '''
    name = models.CharField(max_length=100, unique=True)
    facility = models.ForeignKey(Facility)

    class Meta:
        app_label = 'tardis_portal'
        verbose_name_plural = 'Instruments'

    def __unicode__(self):
        return self.name

    def getParameterSets(self, schemaType=None):
        '''Return the instrument parametersets associated with this
        instrument.

        '''
        from tardis.tardis_portal.models.parameters import Schema
        if schemaType == Schema.INSTRUMENT or schemaType is None:
            return self.instrumentparameterset_set.filter(
                schema__type=Schema.INSTRUMENT)
        else:
            raise Schema.UnsupportedType

    def _has_change_perm(self, user_obj):
        """
        Instrument objects should only be modified by members of the facility
        managers group.
        """
        return self.facility.manager_group in user_obj.groups.all()
