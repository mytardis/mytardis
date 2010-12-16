# -*- coding: utf-8 -*-
#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
models.py

@author Steve Androulakis
@author Gerson Galang

"""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.utils.safestring import SafeUnicode


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

    def getUserAuthentications(self):
        return self.userAuthentication_set.all()


class GroupAdmin(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)


class UserAuthentication(models.Model):
    LOCALDB_METHOD = 1
    VBL_METHOD = 2
    LDAP_METHOD = 3
    __COMPARISON_CHOICES = (
        (LOCALDB_METHOD, 'Local DB'),
        (VBL_METHOD, 'VBL'),
#        (LDAP_METHOD, 'LDAP')
    )
    userProfile = models.ForeignKey(UserProfile)
    username = models.CharField(max_length=50)
    authenticationMethod = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=LOCALDB_METHOD)


class XSLT_docs(models.Model):

    xmlns = models.URLField(max_length=255, primary_key=True)
    data = models.TextField()

    def __unicode__(self):
        return self.xmlns


class Author(models.Model):

    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class ExperimentManager(models.Manager):

    def all(self, request):
        from django.db.models import Q
        query = Q(public=True)

        if request.user.is_authenticated():
            from django.contrib.sessions.models import Session
            s = Session.objects.get(pk=request.COOKIES['sessionid'])
            backend = s.get_decoded()['_auth_user_backend']

            query |= Q(experimentacl__pluginId=backend,
                       experimentacl__entityId=request.user.id,
                       experimentacl__canRead=True)

        return super(ExperimentManager, self).get_query_set().filter(query)

    def get(self, request, experiment_id):
        experiment = \
            super(ExperimentManager, self).get(pk=experiment_id)

        if experiment.public:
            return experiment

        from django.core.exceptions import PermissionDenied
        if not request.user.is_authenticated():
            raise PermissionDenied

        from django.contrib.sessions.models import Session
        s = Session.objects.get(pk=request.COOKIES['sessionid'])
        backend = s.get_decoded()['_auth_user_backend']

        acl = super(ExperimentManager, self).filter(
            experimentacl__pluginId=backend,
            experimentacl__entityId=request.user.id,
            experimentacl__experiment=experiment,
            experimentacl__canRead=True)

        if acl.count() == 0:
            raise PermissionDenied
        else:
            return experiment

    def owned(self, request):
        if not request.user.is_authenticated():
            return []

        from django.contrib.sessions.models import Session
        s = Session.objects.get(pk=request.COOKIES['sessionid'])
        backend = s.get_decoded()['_auth_user_backend']
        experiments = super(ExperimentManager, self).get_query_set().filter(
            experimentacl__pluginId=user.backend,
            experimentacl__entityId=user.id,
            experimentacl__isOwner=True)


class Experiment(models.Model):

    url = models.URLField(verify_exists=False, max_length=255)
    approved = models.BooleanField()
    title = models.CharField(max_length=400)
    institution_name = models.CharField(max_length=400)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User)
    handle = models.TextField(null=True, blank=True)
    public = models.BooleanField()

    objects = models.Manager() # The default manager.
    safe = ExperimentManager() # The acl-aware specific manager.

    def __unicode__(self):
        return self.title


class Author_Experiment(models.Model):

    experiment = models.ForeignKey(Experiment)
    author = models.ForeignKey(Author)
    order = models.PositiveIntegerField()

    def __unicode__(self):
        return SafeUnicode(self.author.name) + ' | ' \
            + SafeUnicode(self.experiment.id) + ' | ' \
            + SafeUnicode(self.order)

    class Meta:
        ordering = ['order']
        unique_together = (('experiment', 'author'),)


class Dataset(models.Model):

    experiment = models.ForeignKey(Experiment)
    description = models.TextField()

    def __unicode__(self):
        return self.description


class Dataset_File(models.Model):

    dataset = models.ForeignKey(Dataset)
    filename = models.CharField(max_length=400)
    url = models.URLField(max_length=400)
    size = models.CharField(blank=True, max_length=400)
    protocol = models.CharField(blank=True, max_length=10)
    created_time = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.filename


class Schema(models.Model):

    namespace = models.URLField(verify_exists=False, max_length=400)

    def __unicode__(self):
        return self.namespace


class DatafileParameterSet(models.Model):
    schema = models.ForeignKey(Schema)
    dataset_file = models.ForeignKey(Dataset_File)

    def __unicode__(self):
        return self.schema.namespace + " / " + self.dataset_file.filename

    class Meta:
        ordering = ['id']


class DatasetParameterSet(models.Model):
    schema = models.ForeignKey(Schema)
    dataset = models.ForeignKey(Dataset)

    def __unicode__(self):
        return self.schema.namespace + " / " + self.dataset.description

    class Meta:
        ordering = ['id']


class ExperimentParameterSet(models.Model):
    schema = models.ForeignKey(Schema)
    experiment = models.ForeignKey(Experiment)

    def __unicode__(self):
        return self.schema.namespace + " / " + self.experiment.title

    class Meta:
        ordering = ['id']


class ParameterName(models.Model):

    EXACT_VALUE_COMPARISON = 1
    NOT_EQUAL_COMPARISON = 2
    RANGE_COMPARISON = 3
    GREATER_THAN_COMPARISON = 4
    GREATER_THAN_EQUAL_COMPARISON = 5
    LESS_THAN_COMPARISON = 6
    LESS_THAN_EQUAL_COMPARISON = 7
    CONTAINS_COMPARISON = 8
    __COMPARISON_CHOICES = (
        (EXACT_VALUE_COMPARISON, 'Exact value'),
        (CONTAINS_COMPARISON, 'Contains'),
        # TODO: enable this next time if i figure out how to support
        #(NOT_EQUAL_COMPARISON, 'Not equal'),
        (RANGE_COMPARISON, 'Range'),
        (GREATER_THAN_COMPARISON, 'Greater than'),
        (GREATER_THAN_EQUAL_COMPARISON, 'Greater than or equal'),
        (LESS_THAN_COMPARISON, 'Less than'),
        (LESS_THAN_EQUAL_COMPARISON, 'Less than or equal'),
    )

    schema = models.ForeignKey(Schema)
    name = models.CharField(max_length=60)
    full_name = models.CharField(max_length=60)
    units = models.CharField(max_length=60, blank=True)
    is_numeric = models.BooleanField()
    comparison_type = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=EXACT_VALUE_COMPARISON)
    is_searchable = models.BooleanField(default=False)
    # TODO: we'll need to rethink the way choices for drop down menus are
    #       represented in the DB. doing it this way is just a bit wasteful.
    choices = models.CharField(max_length=500, blank=True)

    def __unicode__(self):
        return self.name


class DatafileParameter(models.Model):

    parameterset = models.ForeignKey(DatafileParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        if self.name.is_numeric:
            return 'Datafile Param: %s=%s' % (self.name.name,
                self.numerical_value)
        return 'Datafile Param: %s=%s' % (self.name.name, self.string_value)

    class Meta:
        ordering = ['id']


class DatasetParameter(models.Model):

    parameterset = models.ForeignKey(DatasetParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        if self.name.is_numeric:
            return 'Dataset Param: %s=%s' % (self.name.name,
                self.numerical_value)
        return 'Dataset Param: %s=%s' % (self.name.name, self.string_value)

    class Meta:
        ordering = ['id']


class ExperimentParameter(models.Model):
    parameterset = models.ForeignKey(ExperimentParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        if self.name.is_numeric:
            return 'Experiment Param: %s=%s' % (self.name.name,
                self.numerical_value)
        return 'Experiment Param: %s=%s' % (self.name.name, self.string_value)

    class Meta:
        ordering = ['id']


class XML_data(models.Model):
    datafile = models.OneToOneField(Dataset_File, null=True, blank=True)
    dataset = models.OneToOneField(Dataset, null=True, blank=True)
    experiment = models.OneToOneField(Experiment, null=True, blank=True)
    xmlns = models.URLField(max_length=400)
    data = models.TextField()

    def __unicode__(self):
        return self.xmlns


class ExperimentACL(models.Model):
    OWNER_OWNED = 1
    SYSTEM_OWNED = 2
    __COMPARISON_CHOICES = (
        (OWNER_OWNED, 'Owner-owned'),
        (SYSTEM_OWNED, 'System-owned'),
    )

    pluginId = models.CharField(null=False, blank=False, max_length=30)
    entityId = models.CharField(null=False, blank=False, max_length=320)
    experiment = models.ForeignKey(Experiment)
    canRead = models.BooleanField(default=False)
    canWrite = models.BooleanField(default=False)
    canDelete = models.BooleanField(default=False)
    isOwner = models.BooleanField(default=False)

    # this usually is the end of the embargo period when the experiment
    # becomes eligible to be made public
    # TODO: remove null default value once we've fully implemented embargo!
    effectiveDate = models.DateField(null=True, blank=True)

    # if expiryDate is not set, the experiment will be publicly available
    # as long as the effectiveDate is met
    expiryDate = models.DateField(null=True, blank=True)
    aclOwnershipType = models.IntegerField(
        choices=__COMPARISON_CHOICES, default=OWNER_OWNED)

    def __unicode__(self):
        return '%i | %s' % (self.experiment.id, self.experiment.title)

    class Meta:
        ordering = ['experiment__id']


class Equipment(models.Model):
    key = models.CharField(unique=True, max_length=30)
    dataset = models.ManyToManyField(Dataset, null=True, blank=True)
    description = models.TextField(blank=True)
    make = models.CharField(max_length=60, blank=True)
    model = models.CharField(max_length=60, blank=True)
    type = models.CharField(max_length=60, blank=True)
    serial = models.CharField(max_length=60, blank=True)
    comm = models.DateField(null=True, blank=True)
    decomm = models.DateField(null=True, blank=True)
    url = models.URLField(null=True, blank=True, verify_exists=False, max_length=255)

    def __unicode__(self):
        return self.key
