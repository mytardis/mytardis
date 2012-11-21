#
# Copyright (c) 2012, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
#


from django.db import models

DEFAULT_USER_PRIORITY = 2
DEFAULT_GROUP_PRIORITY = 2

class UserPriority(models.Model):
    """
    This class represents Users whose datafiles should be given 
    higher (or lower) priority when scoring files for migration
    """

    from django.contrib.auth.models import User
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

    from django.contrib.auth.models import Group
    group = models.ForeignKey(Group, unique=True)
    priority = models.IntegerField()

    class Meta:
        app_label = 'migration'


def get_group_priority(group):
    try:
        return GroupPriority.objects.get(group=group).priority
    except GroupPriority.DoesNotExist:
        return DEFAULT_GROUP_PRIORITY
