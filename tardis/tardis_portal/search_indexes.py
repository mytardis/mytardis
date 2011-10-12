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
from haystack.indexes import *
from haystack import site
from models import Dataset, Experiment, Dataset_File, \
    DatafileParameter, DatasetParameter, ExperimentParameter, \
    ParameterName, Schema
from django.db.utils import DatabaseError
import logging


logger = logging.getLogger(__name__)

# This is a text index so any numeric fields 
# will default to being rounded to ints
# as there's no real intuitive way to do
# text search on floats etc.
#
# NOTE: Datatypes of paramternames are a bit of a circus (e.g. EPN is a string)
# so this function tries to do the most intelligent possible thing for each
# situation.
#
# For non NUMERIC types, check if string can be converted to a float. If so, then it's a string representation
# if a number and should be converted to a number. If that fails, it's probably a string and 
# can go in as is. If converted to a float, see the steps below for numeric types.
#
# For NUMERIC types, convert to an int to remove decimal points. Text search for
# the number '3.12159' probably isn't very handy so assume that if someone has specified
# this field as text searchable, then it's actually in int.
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
    
    return  int(val)

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

#
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
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        # catch 
        try:    
            for n in [pn for pn in ParameterName.objects.all() if pn.datafileparameter_set.count() and pn.is_searchable is True]:
                attrs['datafile_' + n.name] = _getDataType(n)
        except DatabaseError:
            pass
        return super(GetDatasetFileParameters, cls).__new__(cls, name, bases, attrs)

class DatasetFileIndex(RealTimeSearchIndex):
    
    __metaclass__ = GetDatasetFileParameters
    
    text=NgramField(document=True)
    datafile_filename  = CharField(model_attr='filename')
    dataset_id_stored = IntegerField(model_attr='dataset__pk', indexed=False)
    dataset_description_stored = CharField(model_attr='dataset__description', indexed=False)
    experiment_id_stored = IntegerField(model_attr='dataset__experiment__pk', indexed=False)
    experiment_title_stored = CharField(model_attr='dataset__experiment__title', indexed=False)
    experiment_description_stored = CharField(model_attr='dataset__experiment__description', indexed=False)
    experiment_created_time_stored = DateTimeField(model_attr='dataset__experiment__created_time', indexed=False)
    experiment_start_time_stored = DateTimeField(model_attr='dataset__experiment__start_time', indexed=False, default=None)
    experiment_end_time_stored = DateTimeField(model_attr='dataset__experiment__end_time', indexed=False, default=None)
    experiment_institution_name_stored = CharField(model_attr='dataset__experiment__institution_name', indexed=False)
    experiment_update_time_stored = DateTimeField(model_attr='dataset__experiment__update_time', indexed=False)
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetFileIndex, self).prepare(obj)
        
        # 
        # prepare the free text field and also add all searchable
        # soft parameters as field-searchable fields
        #
        
        # Default fields to be added to free text index to  be used in the 
        # absence of valid settings
        freetext_params = ['filename']
        
        text_list = []
        text_list.extend([val for key, val in obj.__dict__.items() if key in freetext_params])
        
        # Get all searchable soft params for this experiment that
        # appear in the list of soft params to be indexed for
        # full text search
        #
        # NOTE: soft params that are flagged as not being 
        # searchable will be silently ignored even if they
        # have an associated FreeTextSearchField
        
        params = DatafileParameter.objects.filter(
                parameterset__dataset_file__id=obj.id,
                name__is_searchable=True,
                name__freetextsearchfield__isnull=False)
        
        text_list.extend(map(toIntIfNumeric, params))
        
        # Always convert to strings as this is a text index
        self.prepared_data['text'] = ' '.join(map(str,text_list))

        # add all soft parameters listed as searchable as in field search
        for par in DatafileParameter.objects.filter(
                parameterset__dataset_file__pk=obj.pk, 
                name__is_searchable=True):
            self.prepared_data['datafile_' + par.name.name] = _getParamValue(par) 
        return self.prepared_data

class GetDatasetParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        try:
            for n in [pn for pn in ParameterName.objects.all() if pn.datasetparameter_set.count() and pn.is_searchable is True]:
                attrs['dataset_' + n.name] = _getDataType(n)
        except DatabaseError:
            pass
        return super(GetDatasetParameters, cls).__new__(cls, name, bases, attrs)

class DatasetIndex(OracleSafeIndex):
    
    __metaclass__ = GetDatasetParameters
    
    text=NgramField(document=True)
    dataset_description = CharField(model_attr='description')
    experiment_id_stored = IntegerField(model_attr='experiment__pk', indexed=False)
    experiment_title_stored = CharField(model_attr='experiment__title', indexed=False)
    experiment_description_stored = CharField(model_attr='experiment__description', indexed=False)
    experiment_created_time_stored = DateTimeField(model_attr='experiment__created_time', indexed=False)
    experiment_start_time_stored = DateTimeField(model_attr='experiment__start_time', indexed=False, default=None)
    experiment_end_time_stored = DateTimeField(model_attr='experiment__end_time', indexed=False, default=None)
    experiment_institution_name_stored = CharField(model_attr='experiment__institution_name', indexed=False)
    experiment_update_time_stored = DateTimeField(model_attr='experiment__update_time', indexed=False)
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetIndex, self).prepare(obj)

        # 
        # prepare the free text field and also add all searchable
        # soft parameters as field-searchable fields
        #
        
        # Default fields to be added to free text index to  be used in the 
        # absence of valid settings
        freetext_params = ['description']
        
        text_list = []
        text_list.extend([val for key, val in obj.__dict__.items() if key in freetext_params])
        
        # Get all searchable soft params for this experiment that
        # appear in the list of soft params to be indexed for
        # full text search
        #
        # NOTE: soft params that are flagged as not being 
        # searchable will be silently ignored even if they
        # have an associated FreeTextSearchField
        params = DatasetParameter.objects.filter(
                parameterset__dataset__id=obj.id,
                name__is_searchable=True,
                name__freetextsearchfield__isnull=False)
        
        text_list.extend(map(toIntIfNumeric, params))
        
        # Always convert to strings as this is a text index
        self.prepared_data['text'] = ' '.join(map(str,text_list))

        # add all soft parameters listed as searchable as in field search
        for par in DatasetParameter.objects.filter(
                parameterset__dataset__pk=obj.pk, 
                name__is_searchable=True):
            self.prepared_data['dataset_'  + par.name.name] = _getParamValue(par)
        return self.prepared_data

class GetExperimentParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):
        
        # dynamically add all the searchable parameter fields
        try:
            pns = ParameterName.objects.filter(schema__type=Schema.EXPERIMENT, is_searchable=True)
            for n in pns:
                attrs['experiment_' + n.name] = _getDataType(n)
        except DatabaseError:
            pass 
        return super(GetExperimentParameters, cls).__new__(cls, name, bases, attrs)

class ExperimentIndex(OracleSafeIndex):
    
    __metaclass__ = GetExperimentParameters

    text= NgramField(document=True)
    experiment_id_stored = IntegerField(model_attr='pk', indexed=False)
    experiment_description = CharField(model_attr='description')
    experiment_title = CharField(model_attr='title')
    experiment_created_time = DateTimeField(model_attr='created_time')
    experiment_start_time = DateTimeField(model_attr='start_time', default=None)
    experiment_end_time = DateTimeField(model_attr='end_time', default=None)
    experiment_update_time = DateTimeField(model_attr='update_time', default=None)
    experiment_institution_name = CharField(model_attr='institution_name', default=None)
    experiment_creator=CharField(model_attr='created_by__username')
    experiment_institution_name=CharField(model_attr='institution_name')
    experiment_authors = MultiValueField()

    def prepare_experiment_authors(self, obj):
        return [a.author for a in obj.author_experiment_set.all()]

    def prepare(self,obj):
        self.prepared_data = super(ExperimentIndex, self).prepare(obj)
        
        # 
        # prepare the free text field and also add all searchable
        # soft parameters as field-searchable fields
        #
        
        # Default fields to be added to free text index to  be used in the 
        # absence of valid settings
        freetext_params = ['title', 'description', 'institution_name']
        
        text_list = []
        text_list.extend([val for key, val in obj.__dict__.items() if key in freetext_params])
        
        # Get all searchable soft params for this experiment that
        # appear in the list of soft params to be indexed for
        # full text search
        #
        # NOTE: soft params that are flagged as not being 
        # searchable will be silently ignored if specified
        # in the settings
        params = ExperimentParameter.objects.filter(
                parameterset__experiment__id=obj.id,
                name__is_searchable=True,
                name__freetextsearchfield__isnull=False)


        
        text_list.extend(map(toIntIfNumeric, params))
        
        # add all authors to the free text search
        text_list.extend(self.prepare_experiment_authors(obj))
        
        # Always convert to strings as this is a text index
        self.prepared_data['text'] = ' '.join(map(str,text_list))
        
        # add all soft parameters listed as searchable as in field search
        for par in ExperimentParameter.objects.filter(
                        parameterset__experiment__id=obj.id, 
                        name__is_searchable=True):
	        self.prepared_data['experiment_' + par.name.name] = _getParamValue(par)

        return self.prepared_data

site.register(Dataset_File, DatasetFileIndex)
site.register(Dataset, DatasetIndex)
site.register(Experiment, ExperimentIndex)
