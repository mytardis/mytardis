from django.db import models

import logging
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

    name = models.CharField(max_length=400, unique=True, blank=False)
    url  = models.URLField(
        verify_exists=True,
        max_length=2000,
        blank=False,
        unique=True,
        help_text="Link to document outlining licensing details.")
    internal_description = models.TextField(blank=False)
    image_url = models.URLField(verify_exists=True, max_length=2000, blank=True)
    allows_distribution = models.BooleanField(
        default=False,
        help_text="Does this license provide distribution rights?")

    def __unicode__(self):
        return self.name

