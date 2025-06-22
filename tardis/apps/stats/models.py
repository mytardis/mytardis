from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Stat(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class UserStat(models.Model):
    date = models.DateField(null=False, default=timezone.now, db_index=True)
    user = models.ForeignKey(User, null=False, db_index=True, on_delete=models.CASCADE)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)
    str_value = models.TextField(null=True, blank=True)
    int_value = models.IntegerField(null=True, blank=True)
    bigint_value = models.BigIntegerField(null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("date", "user", "stat")
