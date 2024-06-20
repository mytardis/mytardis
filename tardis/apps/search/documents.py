import logging
from django.conf import settings

from django.contrib.auth.models import User
from elasticsearch_dsl import analysis, analyzer
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from tardis.tardis_portal.models import Dataset, Experiment, \
    DataFile, Instrument, ObjectACL


logger = logging.getLogger(__name__)


elasticsearch_index_settings = getattr(settings, 'ELASTICSEARCH_DSL_INDEX_SETTINGS', {
    'number_of_shards': 1,
    'number_of_replicas': 0
})
elasticsearch_parallel_index_settings = getattr(settings, 'ELASTICSEARCH_PARALLEL_INDEX_SETTINGS', {})

trigram = analysis.tokenizer('trigram', 'ngram', min_gram=3, max_gram=3)

analyzer = analyzer(
    "analyzer",
    tokenizer=trigram,
    filter='lowercase',
)


@registry.register_document
class ExperimentDocument(Document):
    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(self, actions=actions,
                               **elasticsearch_parallel_index_settings)

    class Index:
        name = 'experiments'
        settings = elasticsearch_index_settings

    id = fields.IntegerField()
    title = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    public_access = fields.IntegerField()
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    update_time = fields.DateField()
    institution_name = fields.KeywordField()
    created_by = fields.ObjectField(properties={
        'username': fields.KeywordField()
    })
    objectacls = fields.ObjectField(properties={
        'pluginId': fields.KeywordField(),
        'entityId': fields.KeywordField()
    }
    )

    class Django:
        model = Experiment
        related_models = [User, ObjectACL, DataFile]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.experiment_set.all()
        if isinstance(related_instance, ObjectACL):
            return related_instance.content_object
        if isinstance(related_instance, DataFile):
            related_instance.dataset.experiments.all()
        return None


@registry.register_document
class DatasetDocument(Document):
    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(self, actions=actions,
                               **elasticsearch_parallel_index_settings)

    class Index:
        name = 'dataset'
        settings = elasticsearch_index_settings

    id = fields.IntegerField()
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    experiments = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': fields.TextField(
            fields={'raw': fields.KeywordField()
                    }
        ),
        'objectacls': fields.ObjectField(properties={
            'pluginId': fields.KeywordField(),
            'entityId': fields.KeywordField()
        }
        ),
        'public_access': fields.IntegerField()
    }
    )
    instrument = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(
            fields={'raw': fields.KeywordField()},
        )
    }
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()

    class Django:
        model = Dataset
        related_models = [Experiment, Instrument]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Experiment):
            return related_instance.datasets.all()
        if isinstance(related_instance, Instrument):
            return related_instance.dataset_set.all()
        return None


@registry.register_document
class DataFileDocument(Document):
    def parallel_bulk(self, actions, **kwargs):
        Document.parallel_bulk(self, actions=actions,
                               **elasticsearch_parallel_index_settings)

    class Index:
        name = 'datafile'
        settings = elasticsearch_index_settings

    filename = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    created_time = fields.DateField()
    modification_time = fields.DateField()
    dataset = fields.NestedField(properties={
        'id': fields.IntegerField(),
    })

    experiments = fields.ObjectField()

    def prepare_experiments(self, instance):
        experiments = []
        exps = instance.dataset.experiments.all()
        for exp in exps:
            exp_dict = {}
            exp_dict['id'] = exp.id
            exp_dict['public_access'] = exp.public_access
            oacls = exp.objectacls.all().values('entityId', 'pluginId')
            exp_dict['objectacls'] = list(oacls)
            experiments.append(exp_dict)
        return experiments

    class Django:
        model = DataFile
        related_models = [Dataset, Experiment]
        queryset_pagination = 5000 # same as chunk_size

    def get_queryset(self):
        return super().get_queryset().select_related('dataset')

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Dataset):
            return related_instance.datafile_set.all()
        if isinstance(related_instance, Experiment):
            return DataFile.objects.filter(dataset__experiments=related_instance)
        return None
