from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder

# pylint: disable=C0412
if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
    from .fields import JSONField
elif "mysql" in settings.DATABASES["default"]["ENGINE"]:
    # pylint: disable=E0401
    from django_mysql.models import JSONField
else:
    from django.contrib.postgres.fields import JSONField


class Action(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Log(models.Model):
    class Meta:
        ordering = ["-timestamp"]

    timestamp = models.DateTimeField(null=False, default=timezone.now, db_index=True)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True)
    obj = GenericForeignKey("content_type", "object_id")
    extra = JSONField(DjangoJSONEncoder)
