# -*- coding: utf-8 -*-
# pylint: disable=R0204

#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
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

'''
search indexes for single search

.. moduleauthor:: Shaun O'Keefe  <shaun.okeefe@versi.edu.au>

'''
import logging
import os
import datetime
from haystack import indexes

from tardis.tardis_portal.models import DataFile, Dataset, Experiment

logger = logging.getLogger(__name__)


class ExperimentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    experiment_id_stored = indexes.IntegerField(model_attr='id')
    experiment_title = indexes.CharField(model_attr='title')
    experiment_description = indexes.CharField(model_attr='description')
    experiment_created_time = indexes.DateTimeField(model_attr='created_time')
    experiment_start_time = indexes.DateTimeField(model_attr='start_time', default=None)
    experiment_end_time = indexes.DateTimeField(model_attr='end_time', default=None)
    experiment_update_time = indexes.DateTimeField(model_attr='update_time', default=None)
    experiment_institution_name = indexes.CharField(model_attr='institution_name', default=None)
    experiment_creator=indexes.CharField(model_attr='created_by__username')
    experiment_author = indexes.MultiValueField()

    def prepare_text(self, obj):
        return '{} {}'.format(obj.title, obj.description)

    def prepare_experimentauthor(self, obj):
        return [author.author for author in obj.experimentauthor_set.all()]

    def get_model(self):
        return Experiment

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(created_time__lte=datetime.datetime.now())


class DatasetIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    experiment_id_stored = indexes.MultiValueField(indexed=True, stored=True) #indexes.IntegerField(model_attr='experiments', indexed=True)
    dataset_id_stored = indexes.IntegerField(model_attr='id') #changed
    dataset_description = indexes.CharField(model_attr='description')

    def prepare_text(self, obj):
        return obj.description

    def prepare_experiment_id_stored(self, obj):
        return [exp.id for exp in obj.experiments.all()]

    def get_model(self):
        return Dataset


class DataFileIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    datafile_filename = indexes.CharField(model_attr='filename')
    experiment_id_stored = indexes.MultiValueField(indexed=True, stored=True)
    dataset_id_stored = indexes.IntegerField(model_attr='dataset__id')

    def prepare_text(self, obj):
        return os.path.join(obj.directory or '', obj.filename)

    def prepare_experiment_id_stored(self, obj):
        return [exp.id for exp in obj.dataset.experiments.all()]

    def get_model(self):
        return DataFile
