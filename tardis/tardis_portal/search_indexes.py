from haystack.indexes import *
from haystack import site
from models import Dataset 
from models import Experiment
from models import Dataset_File

class DatasetFileIndex(SearchIndex):
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
    experiment_update_time_stored = DateTimeField(model_attr='update_time', indexed=False)
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetFileIndex, self).prepare(obj)
        self.prepared_data['text'] = obj.filename
        return self.prepared_data

class DatasetIndex(SearchIndex):
    text = CharField(document=True)
    dataset_description = CharField(model_attr='description')
    experiment_id_stored = IntegerField(model_attr='experiment__pk', indexed=False)
    experiment_title_stored = CharField(model_attr='experiment__title', indexed=False)
    experiment_description_stored = CharField(model_attr='experiment__description', indexed=False)
    experiment_created_time_stored = DateTimeField(model_attr='experiment__created_time', indexed=False)
    experiment_start_time_stored = DateTimeField(model_attr='experiment__start_time', indexed=False)
    experiment_end_time_stored = DateTimeField(model_attr='experiment__end_time', indexed=False)
    experiment_institution_name_stored = CharField(model_attr='experiment__institution_name', indexed=False)
    experiment_update_time_stored = DateTimeField(model_attr='update_time', indexed=False)
    
    def prepare(self, obj):
        self.prepared_data = super(DatasetIndex, self).prepare(obj)
        self.prepared_data['text'] = obj.description
        return self.prepared_data

class ExperimentIndex(SearchIndex):
    text=CharField(document=True)
    experiment_description = CharField(model_attr='description')
    experiment_title = CharField(model_attr='title')
    experiment_created_time = DateTimeField(model_attr='created_time')
    experiment_start_time = DateTimeField(model_attr='start_time')
    experiment_end_time = DateTimeField(model_attr='end_time')
    experiment_update_time = DateTimeField(model_attr='update_time')
    experiment_institution_name = CharField(model_attr='institution_name')

    def prepare(self,obj):
            self.prepared_data = super(ExperimentIndex, self).prepare(obj)
            self.prepared_data['text'] = ' '.join([obj.title, obj.description])
            return self.prepared_data

site.register(Dataset_File, DatasetFileIndex)
site.register(Dataset, DatasetIndex)
site.register(Experiment, ExperimentIndex)
