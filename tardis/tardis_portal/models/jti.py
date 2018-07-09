import logging

from django.db import models
from django.utils.safestring import SafeText
from django.utils.encoding import python_2_unicode_compatible

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class JTI(models.Model):
    jti = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'tardis_portal'

    def __str__(self):
        return SafeText(self.jti) + ' | ' \
            + SafeText(self.created_time)
