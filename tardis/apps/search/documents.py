import logging

from django.contrib.auth.models import User
from elasticsearch_dsl import analysis, analyzer
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from tardis.tardis_portal.models import Project, Dataset, Experiment, \
    DataFile, Instrument, ObjectACL, ExperimentParameter, ProjectParameter, \
    DatasetParameter, DatafileParameter


logger = logging.getLogger(__name__)


trigram = analysis.tokenizer('trigram', 'nGram', min_gram=3, max_gram=3)

analyzer = analyzer(
    "analyzer",
    tokenizer=trigram,
    filter='lowercase',
)



@registry.register_document
class ProjectDocument(Document):
    class Index:
        name = 'project'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    id = fields.KeywordField()
    name = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    #public_access = fields.IntegerField()
    start_date = fields.DateField()
    end_date = fields.DateField()
    institution = fields.ObjectField(properties={
        'name': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )
    })
    lead_researcher = fields.ObjectField(properties={
        'username': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )
    })
    objectacls = fields.ObjectField(properties={
        'pluginId': fields.StringField(),
        'entityId': fields.StringField()
    })
    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = Project
        related_models = [User, ObjectACL]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.project_set.all()
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_type == 'project':
                return related_instance.content_object
        return None


@registry.register_document
class ExperimentDocument(Document):
    class Index:
        name = 'experiment'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    id = fields.KeywordField()
    title = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    #public_access = fields.IntegerField()
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    update_time = fields.DateField()
    #institution_name = fields.StringField()
    created_by = fields.ObjectField(properties={
        'username': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )
    })
    project = fields.NestedField(properties={
        'id': fields.KeywordField()
    })
    objectacls = fields.ObjectField(properties={
        'pluginId': fields.StringField(),
        'entityId': fields.StringField()
    })
    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = Experiment
        related_models = [User, ObjectACL]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.experiment_set.all()
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_type == 'experiment':
                return related_instance.content_object
        return None


@registry.register_document
class DatasetDocument(Document):
    class Index:
        name = 'dataset'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    id = fields.KeywordField()
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    experiments = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'project': fields.NestedField(properties={
            'id': fields.KeywordField()
        })
    })
    objectacls = fields.ObjectField(properties={
            'pluginId': fields.StringField(),
            'entityId': fields.StringField()
        })
    instrument = fields.ObjectField(properties={
        'id': fields.KeywordField(),
        'name': fields.TextField(
            fields={'raw': fields.KeywordField()},
        )}
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()
    tags = fields.StringField(attr='tags_for_indexing')

    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = Dataset
        related_models = [Experiment, Instrument, ObjectACL]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Experiment):
            return related_instance.datasets.all()
        if isinstance(related_instance, Instrument):
            return related_instance.dataset_set.all()
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_type == 'dataset':
                return related_instance.content_object
        return None


@registry.register_document
class DataFileDocument(Document):
    class Index:
        name = 'datafile'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}
    id = fields.KeywordField()
    filename = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer)
    created_time = fields.DateField()
    modification_time = fields.DateField()
    dataset = fields.NestedField(properties={
        'id': fields.KeywordField(),
        'experiments': fields.NestedField(properties={
            'id': fields.KeywordField(),
            'project':fields.NestedField(properties={
                'id': fields.KeywordField()
            }),
        }),
    })
    objectacls = fields.ObjectField(properties={
            'pluginId': fields.StringField(),
            'entityId': fields.StringField()
        })

    parameters = fields.NestedField(attr='getParametersforIndexing', properties={
        'string' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.StringField(),
            'sensitive': fields.BooleanField()
        }),
        'numerical' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.FloatField(),
            'sensitive': fields.BooleanField()
        }),
        'datetime' : fields.NestedField(properties = {
            'pn_id': fields.KeywordField(),
            'value': fields.DateField(),
            'sensitive': fields.BooleanField()
        })
    })

    def prepare_parameters(self, instance):
        return dict(instance.getParametersforIndexing())

    class Django:
        model = DataFile
        related_models = [Dataset, Experiment, ObjectACL]
        queryset_pagination = 100000

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.datafile_set.all()
        if isinstance(related_instance, Experiment):
            return DataFile.objects.filter(dataset__experiments=related_instance)
        if isinstance(related_instance, ObjectACL):
            if related_instance.content_type == 'datafile':
                return related_instance.content_object
        return None
