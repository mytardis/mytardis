import logging
from itertools import chain

from django.db import models

logger = logging.getLogger(__name__)


class License(models.Model):
    '''
    Represents a licence for experiment content.

    Instances should provide enough detail for both researchers to select the
    licence, and for the users of their data to divine correct usage of
    experiment content.

    (Non-US developers: We're using US spelling in the code.)
    '''

    class Meta:
        app_label = 'tardis_portal'

    name = models.CharField(max_length=255, unique=True, blank=False)
    url = models.URLField(
        max_length=255,
        blank=False,
        unique=False,
        help_text="Link to document outlining licensing details.")
    internal_description = models.TextField(blank=False)
    image_url = models.URLField(max_length=255, blank=True)
    allows_distribution = models.BooleanField(
        default=False,
        help_text="Does this license provide distribution rights?")
    is_active = models.BooleanField(
        default=True,
        help_text="Can experiments continue to select this license?")

    def __str__(self):
        return self.name

    @classmethod
    def get_suitable_licenses(cls, public_access_method=None):
        def with_none(seq):
            return chain([cls.get_none_option_license()], seq)
        # If no method specify, return all
        if public_access_method is None:
            return with_none(cls.objects.filter(is_active=True))
        # Otherwise, ask Experiment to put it in terms we understand
        from .experiment import Experiment
        if Experiment.public_access_implies_distribution(public_access_method):
            # Only licences which allow distribution
            return cls.objects.filter(is_active=True, allows_distribution=True)
        # Only licenses which don't allow distribution (including none)
        return with_none(cls.objects.filter(is_active=True,
                                            allows_distribution=False))

    @classmethod
    def get_none_option_license(cls):
        url = 'http://en.wikipedia.org/wiki/Copyright#Exclusive_rights'
        desc = '''
        No license is explicitly specified. You implicitly retain all rights
        under copyright.
        '''
        return License(id='',
                       name='Unspecified License',
                       internal_description=desc,
                       url=url,
                       allows_distribution=False)
