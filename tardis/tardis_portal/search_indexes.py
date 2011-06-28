from haystack.indexes import *
from haystack import site
from models import Dataset 
from models import Experiment
from models import Dataset_File
from models import DatafileParameter 
from models import DatasetParameter
from models import ExperimentParameter 
from models import ParameterName


class GetDatasetFileParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        for n in [pn.name for pn in ParameterName.objects.all() if pn.datafileparameter_set.count() and pn.is_searchable is True]:
        #for dp in DatafileParameter.objects.filter(name__is_searchable=True):
            attrs['datasetfile_' + n] = CharField()# (ExperimentIndex, 'experiment_' + pn.name,  CharField())
        
        return super(GetDatasetFileParameters, cls).__new__(cls, name, bases, attrs)

class DatasetFileIndex(SearchIndex):
    
    #__metaclass__ = GetDatasetFileParameters
    
    text = CharField(document=True)
    datasetfile_filename  = CharField(model_attr='filename')
    dataset_id_stored = IntegerField(model_attr='dataset__pk', indexed=False)
    dataset_description_stored = CharField(model_attr='dataset__description', indexed=False)
    experiment_id_stored = IntegerField(model_attr='dataset__experiment__pk', indexed=False)
    experiment_title_stored = CharField(model_attr='dataset__experiment__title', indexed=False)
    experiment_description_stored = CharField(model_attr='dataset__experiment__description', indexed=False)
    experiment_created_time_stored = DateTimeField(model_attr='dataset__experiment__created_time', indexed=False)
    experiment_start_time_stored = DateTimeField(model_attr='dataset__experiment__start_time', indexed=False)
    experiment_end_time_stored = DateTimeField(model_attr='dataset__experiment__end_time', indexed=False)
    experiment_institution_name_stored = CharField(model_attr='dataset__experiment__institution_name', indexed=False)
    experiment_update_time_stored = DateTimeField(model_attr='dataset__experiment__update_time', indexed=False)
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetFileIndex, self).prepare(obj)
        self.prepared_data['text'] = obj.filename

        for par in DatafileParameter.objects.filter(parameterset__dataset_file__pk=obj.pk).filter(name__is_searchable=True):
        #for par_set in obj.datafileparameterset_set.all():
        #    for par in par_set.datafileparameter_set.filter(name__is_searchable=True):
            self.prepared_data['datasetfile_' + par.name.name] = par.string_value # TODO: add other fields
        return self.prepared_data

class GetDatasetParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        for n in [pn.name for pn in ParameterName.objects.all() if pn.datasetparameter_set.count() and pn.is_searchable is True]:
        #for dp in DatasetParameter.objects.filter(name__is_searchable=True):
            attrs['dataset_' + n] = CharField()# (ExperimentIndex, 'experiment_' + pn.name,  CharField())
        
        return super(GetDatasetParameters, cls).__new__(cls, name, bases, attrs)

class DatasetIndex(SearchIndex):
    
    __metaclass__ = GetDatasetParameters
    
    text = CharField(document=True)
    dataset_description = CharField(model_attr='description')
    experiment_id_stored = IntegerField(model_attr='experiment__pk', indexed=False)
    experiment_title_stored = CharField(model_attr='experiment__title', indexed=False)
    experiment_description_stored = CharField(model_attr='experiment__description', indexed=False)
    experiment_created_time_stored = DateTimeField(model_attr='experiment__created_time', indexed=False)
    experiment_start_time_stored = DateTimeField(model_attr='experiment__start_time', indexed=False)
    experiment_end_time_stored = DateTimeField(model_attr='experiment__end_time', indexed=False)
    experiment_institution_name_stored = CharField(model_attr='experiment__institution_name', indexed=False)
    experiment_update_time_stored = DateTimeField(model_attr='experiment__update_time', indexed=False)
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetIndex, self).prepare(obj)
        self.prepared_data['text'] = obj.description

        #for name in [pn.name for pn in ParameterName.objects.all() if pn.datasetparameter_set.count() and pn.is_searchable is True]:
        for par in DatasetParameter.objects.filter(parameterset__dataset__pk=obj.pk).filter(name__is_searchable=True):
        #for par_set in obj.datasetparameterset_set.all():
        #    for par in par_set.datasetparameter_set.filter(name__is_searchable=True):
            self.prepared_data['dataset_'  + par.name.name] = par.string_value # TODO: add other fields
        return self.prepared_data

class GetExperimentParameters(SearchIndex.__metaclass__):
    def __new__(cls, name, bases, attrs):

        # dynamically add all the searchable parameter fields
        for n in [pn.name for pn in ParameterName.objects.all() if pn.experimentparameter_set.count() and pn.is_searchable is True]:
        #for ep in ExperimentParameter.objects.filter(name__is_searchable=True):
            attrs['experiment_' + n] = CharField()# (ExperimentIndex, 'experiment_' + pn.name,  CharField())
        
        return super(GetExperimentParameters, cls).__new__(cls, name, bases, attrs)

class ExperimentIndex(SearchIndex):
    
    __metaclass__ = GetExperimentParameters

    text=CharField(document=True)
    experiment_description = CharField(model_attr='description')
    experiment_title = CharField(model_attr='title')
    experiment_created_time = DateTimeField(model_attr='created_time')
    experiment_start_time = DateTimeField(model_attr='start_time')
    experiment_end_time = DateTimeField(model_attr='end_time')
    experiment_update_time = DateTimeField(model_attr='update_time')
    experiment_institution_name = CharField(model_attr='institution_name')
    experiment_creator=CharField(model_attr='created_by__username')
    experiment_institution_name=CharField(model_attr='institution_name')
    experiment_authors = MultiValueField()


    def prepare_experiment_authors(self, obj):
        return [a for a in obj.author_experiment_set.all()]

    def prepare(self,obj):
            self.prepared_data = super(ExperimentIndex, self).prepare(obj)
            self.prepared_data['text'] = ' '.join([obj.title, obj.description])
        
            for par in ExperimentParameter.objects.filter(parameterset__experiment__pk=obj.pk).filter(name__is_searchable=True):
            #for par_set in obj.experimentparameterset_set.all():
                #for par in par_set.experimentparameter_set.filter(name__is_searchable=True):
                self.prepared_data['experiment_' + par.name.name] = par.string_value # TODO: add other fields
            return self.prepared_data

site.register(Dataset_File, DatasetFileIndex)
site.register(Dataset, DatasetIndex)
site.register(Experiment, ExperimentIndex)
