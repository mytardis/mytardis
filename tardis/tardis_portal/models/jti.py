from django.db import models
from django.utils.safestring import SafeUnicode

import logging
logger = logging.getLogger(__name__)


class JTI(models.Model):
    jti = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'tardis_portal'

    def __unicode__(self):
        return SafeUnicode(self.jti) + ' | ' \
            + SafeUnicode(self.created_time)
