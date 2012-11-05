from django.db import models
from django.contrib.auth.models import User, Group

DEFAULT_USER_PRIORITY = 2
DEFAULT_GROUP_PRIORITY = 2

class UserPriority(models.Model):
    """
    This class represents Users whose datafiles should be given 
    higher (or lower) priority when scoring files for migration
    """

    user = models.ForeignKey(User, unique=True)
    priority = models.IntegerField()

    class Meta:
        app_label = 'migration'


def get_user_priority(user):
    try:
        return UserPriority.objects.get(user=user).priority
    except UserPriority.DoesNotExist:
        return DEFAULT_USER_PRIORITY


class GroupPriority(models.Model):
    """
    This class represents Groups whose datafiles should be given 
    higher (or lower) priority when scoring files for migration
    """

    group = models.ForeignKey(Group, unique=True)
    priority = models.IntegerField()

    class Meta:
        app_label = 'migration'


def get_group_priority(group):
    try:
        return GroupPriority.objects.get(group=group).priority
    except GroupPriority.DoesNotExist:
        return DEFAULT_GROUP_PRIORITY
