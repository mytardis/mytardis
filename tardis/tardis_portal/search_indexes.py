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
from models import Dataset_File, \
    DatafileParameter, DatasetParameter, ExperimentParameter, \
    ParameterName, Schema
from django.db.utils import DatabaseError
import logging
from django.db import models

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
        return NgramField()

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

class CachedField(SearchField):
    

    def __init__(self, **kwargs):
        
        self.cache = {}
        
        super(CachedField, self).__init__(**kwargs)

    def prepare(self, obj):

        fk  = False
        if self.model_attr is not None:
            attrs = self.model_attr.split('__')
            current_obj = obj
            for attr in attrs:
                if not hasattr(current_obj, attr):
                    break
                next_obj = getattr(current_obj, attr, None)
                if not isinstance(next_obj, models.Model):
                    break
                current_obj = next_obj
            if not current_obj is obj:
                pk = current_obj.pk
                fk = True

        if fk and pk in self.cache:
            return self.cache[pk]
        if fk:
            print 'not in cache, so generate it (pk:%d, object: %s, attr: %s)' % (pk, current_obj, self.model_attr)
        result = super(CachedField, self).prepare(obj)
        
        if fk:
            self.cache[pk] = result
        
        return result

class CachedCharField(CachedField, CharField):
    pass

class CachedIntegerField(CachedField, CharField):
    pass

class CachedFloatField(CachedField, CharField):
    pass

class CachedDecimalField(CachedField, CharField):
    pass

class CachedBooleanField(CachedField, CharField):
    pass

class CachedDateField(CachedField, CharField):
    pass

class CachedDateTimeField(CachedField, CharField):
    pass

class CachedMultiValueField(CachedField, CharField):
    pass

class CachedNgramField(CachedField, NgramField):
    pass

class GetDatasetFileParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        try:
            pns = ParameterName.objects.filter(is_searchable=True)
            for pn in pns:
                prefix = ''
                if pn.schema.type == Schema.DATAFILE:
                    prefix = 'datafile_'
                elif pn.schema.type == Schema.DATASET:
                    prefix = 'dataset_'
                elif pn.schema.type == Schema.EXPERIMENT:
                    prefix = 'experiment_'
                else:
                    pass
                attrs[prefix + pn.name] = _getDataType(pn)
        except DatabaseError:
            pass
        
        return super(GetDatasetFileParameters, cls).__new__(cls, name, bases, attrs)

class DatasetFileIndex(RealTimeSearchIndex):
    
    __metaclass__ = GetDatasetFileParameters
    
    text=NgramField(document=True)
    datafile_filename  = NgramField(model_attr='filename')
    
    dataset_id_stored = IntegerField(model_attr='dataset__pk', indexed=True) #changed
    dataset_description = NgramField(model_attr='dataset__description')

    experiment_id_stored = CachedIntegerField(model_attr='dataset__experiment__pk', indexed=True) # changed
    experiment_description = CachedNgramField(model_attr='dataset__experiment__description')
    experiment_title = CachedNgramField(model_attr='dataset__experiment__title')
    experiment_created_time = CachedDateTimeField(model_attr='dataset__experiment__created_time')
    experiment_start_time = CachedDateTimeField(model_attr='dataset__experiment__start_time', default=None)
    experiment_end_time = CachedDateTimeField(model_attr='dataset__experiment__end_time', default=None)
    experiment_update_time = CachedDateTimeField(model_attr='dataset__experiment__update_time', default=None)
    experiment_institution_name = CachedNgramField(model_attr='dataset__experiment__institution_name', default=None)
    experiment_creator= CachedCharField(model_attr='dataset__experiment__created_by__username')
    experiment_institution_name=CachedNgramField(model_attr='dataset__experiment__institution_name')
    experiment_authors = CachedMultiValueField()
   
    exp_cache = {}
    ds_cache = {}
    exp_param_cache = {}
    ds_param_cache = {}
   
    def get_experiment_text(self, obj, exp):
        
        if not exp in self.exp_cache:
            text_list = [exp.title, exp.description, exp.institution_name]
            params = ExperimentParameter.objects.filter(
                    parameterset__experiment__id=exp.id,
                    name__is_searchable=True,
                    name__freetextsearchfield__isnull=False)
            
            text_list.extend(map(toIntIfNumeric, params))
            
            # add all authors to the free text search
            text_list.extend(self.prepare_experiment_authors(obj))
            text_list.extend(self.prepare_experiment_creator(obj))

            self.exp_cache[exp] = ' '.join(map(str,text_list))
        return self.exp_cache[exp]

    def get_dataset_text(self, obj, ds):
        
        if not ds in self.ds_cache:
            text_list = [ds.description]
            params = DatasetParameter.objects.filter(
                    parameterset__dataset__id=ds.id,
                    name__is_searchable=True,
                    name__freetextsearchfield__isnull=False)
            
            text_list.extend(map(toIntIfNumeric, params))
            
            # Always convert to strings as this is a text index
            self.ds_cache[ds] = ' '.join(map(str,text_list))
        return self.ds_cache[ds]

    def get_experiment_params(self, exp):
        if exp not in self.exp_param_cache:
            param_dict = {}
            for par in ExperimentParameter.objects.filter(
                    parameterset__experiment__pk=exp.id, 
                    name__is_searchable=True):
                param_dict['experiment_' + par.name.name] = _getParamValue(par)
   
            self.exp_param_cache[exp] = param_dict

        return self.exp_param_cache[exp]

    def get_dataset_params(self, ds):
        if ds not in self.ds_param_cache:
            param_dict = {}
            for par in DatasetParameter.objects.filter(
                    parameterset__dataset__pk=ds.id, 
                    name__is_searchable=True):
                self.param_dict['dataset_'  + par.name.name] = _getParamValue(par)
            self.ds_param_cache[ds] = param_dict

        return self.ds_param_cache[ds]

    def prepare_experiment_authors(self, obj):
        return [a.author for a in obj.dataset.experiment.author_experiment_set.all()]
    
    def prepare_experiment_creator(self, obj):
        exp = obj.dataset.experiment 
        return ' '.join([exp.created_by.first_name, exp.created_by.last_name,\
                exp.created_by.username, exp.created_by.email]) 
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetFileIndex, self).prepare(obj)
        
        # 
        # prepare the free text field and also add all searchable
        # soft parameters as field-searchable fields
        #
        exp = obj.dataset.experiment
        ds = obj.dataset
        text_list = [exp.title, exp.description, exp.institution_name, ds.description, obj.filename]
        
        
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
        
        exp_text = self.get_experiment_text(obj, exp) 
        ds_text = self.get_dataset_text(obj, ds)
       
        # Always convert to strings as this is a text index
        df_text  = ' '.join(map(str,text_list))
        
        self.prepared_data['text'] = ' '.join([exp_text, ds_text, df_text])

        # add all soft parameters listed as searchable as in field search
        for par in DatafileParameter.objects.filter(
                parameterset__dataset_file__pk=obj.pk, 
                name__is_searchable=True):
            self.prepared_data['datafile_' + par.name.name] = _getParamValue(par) 
        
        self.prepared_data.update(self.get_experiment_params(exp))
        self.prepared_data.update(self.get_dataset_params(ds))
        
        return self.prepared_data

site.register(Dataset_File, DatasetFileIndex)
