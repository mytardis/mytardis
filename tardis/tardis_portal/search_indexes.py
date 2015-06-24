# -*- coding: utf-8 -*-

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
from haystack.indexes import (
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    MultiValueField,
    RealTimeSearchIndex,
    SearchIndex,
)
from haystack import site
from models import DataFile, \
    DatafileParameter, DatasetParameter, ExperimentParameter, \
    ParameterName, Schema
from django.db.utils import DatabaseError
import logging
from django.template.defaultfilters import slugify
import re

logger = logging.getLogger(__name__)


#
# Removes anything unwholesome before text is added to a text field for
# a search document
#
def cleanText(text):
    p = re.compile(r'<.*?>')

    # convert to unicode rather than
    # str. Solr isn't set up to search
    # on unicode, but it will at least
    # harmlessly index it and we can
    # change the configuration later
    # to do the searches.
    clean_text = unicode(text)

    # Remove html tags
    clean_text = p.sub('', clean_text)

    return clean_text


def _underscoreSlug(text):
    return slugify(text).replace('-', '_')

# Take the paramtername and massage it
# into a suitable search field name
# based on the paramtername schema type
# and the paramtername full name


def prepareFieldName(parameter_name):

    prefix = ''
    schema_name = _underscoreSlug(parameter_name.schema.name)
    if parameter_name.schema.type == Schema.DATAFILE:
        prefix = 'datafile'
    elif parameter_name.schema.type == Schema.DATASET:
        prefix = 'dataset'
    elif parameter_name.schema.type == Schema.EXPERIMENT:
        prefix = 'experiment'
    else:
        pass
    slug = _underscoreSlug(parameter_name.full_name)

    return '_'.join([prefix, schema_name, slug])


# This is a text index so any numeric fields
# will default to being rounded to ints
# as there's no real intuitive way to do
# text search on floats etc.
#
# NOTE: Datatypes of paramternames are a bit of a circus (e.g. EPN is a string)
# so this function tries to do the most intelligent possible thing for each
# situation.
#
# For non NUMERIC types, check if string can be converted to a float. If so,
# then it's a string representation if a number and should be converted to a
# number. If that fails, it's probably a string and can go in as is. If
# converted to a float, see the steps below for numeric types.
#
# For NUMERIC types, convert to an int to remove decimal points. Text search
# for the number '3.12159' probably isn't very handy so assume that if someone
# has specified this field as text searchable, then it's actually in int.
#
def toIntIfNumeric(param):
    val = ''
    if not param.name.isNumeric():
        val = _getParamValue(param)
        try:
            val = float(val)
        except (ValueError, TypeError):
            return val

    else:
        val = _getParamValue(param)

    return int(val)


def _getDataType(param_name):
    if param_name.isNumeric():
        return FloatField()
    elif param_name.isDateTime():
        return DateTimeField()
    else:
        return CharField()


def _getParamValue(param):
    if param.name.isNumeric():
        return param.numerical_value
    elif param.name.isDateTime():
        return param.datetime_value
    else:
        return param.string_value


# Overrides the index_queryset function of the basic
# SearchIndex. index_queryset fetches a QuerySet for
# haystack to index. If we're uinsg the OracleSafeManager
# then a regular QuerySet fetched with objects.all will
# be full of deferred models instances. One of the
# offshoots of this is that all the model instances
# will be proxy classes instances, with names like
# Experiment_Deferred_deferredField1_deferredField2 etc.
# This breaks haystack as it checks that each index entry
# returned by search is an instance of one of the
# models registered with the site (This list is generated
# from static class properties and not instances so
# nothing will be deferred). It will look for
# 'Experiment' for example, but finde Experiment_Deferred...
# and will return an empty SearchQuerySet.
#
# We fix this by un-deferring the QuerySets passed to
# Haystack. This doesn't seem to break anything (the
# indexing operation doesn't generate any UNIQUE calls
# to the DB).
#
class OracleSafeIndex(RealTimeSearchIndex):
    def index_queryset(self):
        return self.model._default_manager.all().defer(None)


class GetDatasetFileParameters(SearchIndex.__metaclass__):
    def __new__(mcs, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        try:
            pns = ParameterName.objects.filter(is_searchable=True)
            for pn in pns:
                fn = prepareFieldName(pn)
                attrs[fn] = _getDataType(pn)
        except DatabaseError:
            pass

        return super(GetDatasetFileParameters, mcs).__new__(
            mcs, name, bases, attrs)


class DatasetFileIndex(RealTimeSearchIndex):

    __metaclass__ = GetDatasetFileParameters

    text = CharField(document=True)
    datafile_filename = CharField(model_attr='filename')

    dataset_id_stored = IntegerField(
        model_attr='dataset__pk', indexed=True)  # changed
    dataset_description = CharField(model_attr='dataset__description')

    experiment_id_stored = IntegerField(
        model_attr='dataset__experiment__pk', indexed=True)  # changed
    experiment_description = CharField(
        model_attr='dataset__experiment__description')
    experiment_title = CharField(
        model_attr='dataset__experiment__title')
    experiment_created_time = DateTimeField(
        model_attr='dataset__experiment__created_time')
    experiment_start_time = DateTimeField(
        model_attr='dataset__experiment__start_time', default=None)
    experiment_end_time = DateTimeField(
        model_attr='dataset__experiment__end_time', default=None)
    experiment_update_time = DateTimeField(
        model_attr='dataset__experiment__update_time', default=None)
    experiment_institution_name = CharField(
        model_attr='dataset__experiment__institution_name', default=None)
    experiment_creator = CharField(
        model_attr='dataset__experiment__created_by__username')
    experiment_institution_name = CharField(
        model_attr='dataset__experiment__institution_name')
    experiment_authors = MultiValueField()

    exp_cache = {}
    ds_cache = {}
    exp_param_cache = {}
    ds_param_cache = {}

    def get_experiment_text(self, obj, exp):

        if exp not in self.exp_cache:
            text_list = [exp.title, exp.description, exp.institution_name]
            params = ExperimentParameter.objects.filter(
                parameterset__experiment__id=exp.id,
                name__is_searchable=True,
                name__freetextsearchfield__isnull=False)

            text_list.extend(map(toIntIfNumeric, params))

            # add all authors to the free text search
            text_list.extend(self.prepare_experiment_authors(obj))
            text_list.extend(self.prepare_experiment_creator(obj))
            self.exp_cache[exp] = ' '.join(map(cleanText, text_list))

        return self.exp_cache[exp]

    def get_dataset_text(self, obj, ds):
        ds = obj.dataset

        if ds not in self.ds_cache:
            text_list = [ds.description]
            params = DatasetParameter.objects.filter(
                parameterset__dataset__id=ds.id,
                name__is_searchable=True,
                name__freetextsearchfield__isnull=False)

            text_list.extend(map(toIntIfNumeric, params))

            # Always convert to strings as this is a text index
            self.ds_cache[ds] = ' '.join(map(cleanText, text_list))
        return self.ds_cache[ds]

    def get_experiment_params(self, exp):
        if exp not in self.exp_param_cache:
            param_dict = {}
            for par in ExperimentParameter.objects.filter(
                    parameterset__experiment__pk=exp.id,
                    name__is_searchable=True):
                fn = prepareFieldName(par.name)
                param_dict[fn] = _getParamValue(par)

            self.exp_param_cache[exp] = param_dict

        return self.exp_param_cache[exp]

    def get_dataset_params(self, ds):
        if ds not in self.ds_param_cache:
            param_dict = {}
            for par in DatasetParameter.objects.filter(
                    parameterset__dataset__pk=ds.id,
                    name__is_searchable=True):
                fn = prepareFieldName(par.name)
                param_dict[fn] = _getParamValue(par)
            self.ds_param_cache[ds] = param_dict

        return self.ds_param_cache[ds]

    def prepare_experiment_authors(self, obj):
        return [a.author
                for a in obj.dataset.experiment.experimentauthor_set.all()]

    def prepare_experiment_creator(self, obj):
        exp = obj.dataset.experiment
        return ' '.join([exp.created_by.first_name, exp.created_by.last_name,
                         exp.created_by.username, exp.created_by.email])

    def prepare(self, obj):
        self.prepared_data = super(DatasetFileIndex, self).prepare(obj)

        #
        # prepare the free text field and also add all searchable
        # soft parameters as field-searchable fields
        #
        exp = obj.dataset.experiment
        ds = obj.dataset
        text_list = [obj.filename]

        # Get all searchable soft params for this experiment that
        # appear in the list of soft params to be indexed for
        # full text search
        #
        # NOTE: soft params that are flagged as not being
        # searchable will be silently ignored even if they
        # have an associated FreeTextSearchField

        params = DatafileParameter.objects.filter(
            parameterset__datafile__id=obj.id,
            name__is_searchable=True,
            name__freetextsearchfield__isnull=False)

        text_list.extend(map(toIntIfNumeric, params))

        exp_text = self.get_experiment_text(obj, exp)
        ds_text = self.get_dataset_text(obj, ds)

        # Always convert to strings as this is a text index
        df_text = ' '.join(map(cleanText, text_list))

        self.prepared_data['text'] = ' '.join([exp_text, ds_text, df_text])

        # add all soft parameters listed as searchable as in field search
        for par in DatafileParameter.objects.filter(
                parameterset__datafile__pk=obj.pk,
                name__is_searchable=True):
            fn = prepareFieldName(par.name)
            self.prepared_data[fn] = _getParamValue(par)

        self.prepared_data.update(self.get_experiment_params(exp))
        self.prepared_data.update(self.get_dataset_params(ds))

        for par in DatasetParameter.objects.filter(
                parameterset__dataset__pk=ds.id,
                name__is_searchable=True):
            fn = prepareFieldName(par.name)
            self.prepared_data[fn] = _getParamValue(par)

        return self.prepared_data

site.register(DataFile, DatasetFileIndex)
