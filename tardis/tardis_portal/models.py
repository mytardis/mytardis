#!/usr/bin/env python
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

from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import SafeUnicode


class UserProfile(models.Model):

    authcate_user = models.BooleanField()
    user = models.ForeignKey(User, unique=True)


class XSLT_docs(models.Model):

    xmlns = models.URLField(max_length=255, primary_key=True)
    data = models.TextField()

    def __unicode__(self):
        return self.xmlns


class Author(models.Model):

    name = models.CharField(max_length=255, primary_key=True)

    def __unicode__(self):
        return self.name


class Experiment(models.Model):

    url = models.URLField(verify_exists=False, max_length=255)
    approved = models.BooleanField()
    title = models.CharField(max_length=400)
    institution_name = models.CharField(max_length=400)
    description = models.TextField(blank=True)
    update_time = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User)
    handle = models.TextField(null=True, blank=True)
    public = models.BooleanField()

    def __unicode__(self):
        return self.title


class Experiment_Owner(models.Model):

    experiment = models.ForeignKey(Experiment)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return SafeUnicode(self.experiment.id) + ' | ' \
            + SafeUnicode(self.user.username)


class Author_Experiment(models.Model):

    experiment = models.ForeignKey(Experiment)
    author = models.ForeignKey(Author)
    order = models.PositiveIntegerField()

    def __unicode__(self):
        return SafeUnicode(self.author.name) + ' | ' \
            + SafeUnicode(self.experiment.id) + ' | ' \
            + SafeUnicode(self.order)


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
        return self.name.name

    class Meta:
        ordering = ['id']


class DatasetParameter(models.Model):

    parameterset = models.ForeignKey(DatasetParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.name.name

    class Meta:
        ordering = ['id']


class ExperimentParameter(models.Model):
    parameterset = models.ForeignKey(ExperimentParameterSet)
    name = models.ForeignKey(ParameterName)
    string_value = models.TextField(null=True, blank=True)
    numerical_value = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.name.name

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
