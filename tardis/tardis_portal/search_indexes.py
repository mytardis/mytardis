from haystack.indexes import *
from haystack import site
from models import Dataset 
from models import Experiment
from models import Dataset_File
from models import DatafileParameter 
from models import DatasetParameter 
from models import ExperimentParameter 
from models import ParameterName
from django.db.utils import DatabaseError

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
                attrs['datasetfile_' + n.name] = _getDataType(n)
        except DatabaseError:
            pass
        return super(GetDatasetFileParameters, cls).__new__(cls, name, bases, attrs)

class DatasetFileIndex(RealTimeSearchIndex):
    
    __metaclass__ = GetDatasetFileParameters
    
    text = CharField(document=True)
    datasetfile_filename  = CharField(model_attr='filename')
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
        self.prepared_data['text'] = obj.filename

        for par in DatafileParameter.objects.filter(parameterset__dataset_file__pk=obj.pk).filter(name__is_searchable=True):
            self.prepared_data['datasetfile_' + par.name.name] = _getParamValue(par) 
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
    
    text = CharField(document=True)
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
        self.prepared_data['text'] = obj.description

        for par in DatasetParameter.objects.filter(parameterset__dataset__pk=obj.pk).filter(name__is_searchable=True):
            self.prepared_data['dataset_'  + par.name.name] = _getParamValue(par)
        return self.prepared_data

class GetExperimentParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        try:
            for n in [pn for pn in ParameterName.objects.all() if pn.experimentparameter_set.count() and pn.is_searchable is True]:
                attrs['experiment_' + n.name] = _getDataType(n)
        except DatabaseError:
            pass
        
        return super(GetExperimentParameters, cls).__new__(cls, name, bases, attrs)

class ExperimentIndex(OracleSafeIndex):
    
    __metaclass__ = GetExperimentParameters

    text=CharField(document=True)
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
        beamline = '' 
        try:
           ep = ExperimentParameter.objects.get(name__name='beamline', parameterset__experiment__id=obj.id, name__is_searchable=True)
           beamline = ep.string_value
        except:
 	    # No beamline soft paramter set for this experiment
            print 'skipping beamline index for experiment id %d (no beamline parameter sepecified)' % (obj.id)

        text_list = [obj.title, obj.description, beamline]
        text_list.extend(self.prepare_experiment_authors(obj))
        self.prepared_data['text'] = ' '.join(text_list)

        for par in ExperimentParameter.objects.filter(parameterset__experiment__pk=obj.pk).filter(name__is_searchable=True):
	    self.prepared_data['experiment_' + par.name.name] = _getParamValue(par)
        return self.prepared_data

site.register(Dataset_File, DatasetFileIndex)
site.register(Dataset, DatasetIndex)
site.register(Experiment, ExperimentIndex)
