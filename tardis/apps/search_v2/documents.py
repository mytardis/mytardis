import logging

from django.contrib.auth.models import User
from elasticsearch_dsl import analysis, analyzer
from django_elasticsearch_dsl import DocType, Index, fields

from tardis.tardis_portal.models import Dataset, Experiment, \
    DataFile, Instrument


logger = logging.getLogger(__name__)


trigram = analysis.tokenizer('trigram', 'nGram', min_gram=3, max_gram=3)

analyzer = analyzer(
    "analyzer",
    tokenizer=trigram,
    filter='lowercase',
)


experiment = Index('experiments')

experiment.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@experiment.doc_type
class ExperimentDocument(DocType):

    id = fields.IntegerField()
    title = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    description = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    update_time = fields.DateField()
    institution_name = fields.StringField()
    created_by = fields.ObjectField(properties={
        'username': fields.StringField(
            fields={'raw': fields.KeywordField()},
        )
    })

    class Meta:
        model = Experiment
        related_models = [User]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, User):
            return related_instance.experiment_set.all()


dataset = Index('dataset')

dataset.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@dataset.doc_type
class DatasetDocument(DocType):
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
        )
    }
    )
    instrument = fields.ObjectField(properties={
        'name': fields.TextField(
        fields={'raw': fields.KeywordField()},
        )
    }
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()

    class Meta:
        model = Dataset
        related_models = [Experiment, Instrument]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Experiment):
            return related_instance.datasets.all()
        elif isinstance(related_instance, Instrument):
            return related_instance.dataset_set.all()
        return


datafile = Index('datafile')

datafile.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@datafile.doc_type
class DataFileDocument(DocType):
    filename = fields.TextField(
        fields={'raw': fields.KeywordField()},
        analyzer=analyzer
    )
    created_time = fields.DateField()
    modification_time = fields.DateField()
    dataset = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'description': fields.TextField(
            fields={'raw': fields.KeywordField()}
        )
    }

    )

    class Meta:
        model = DataFile
        related_models = [Dataset]
        queryset_pagination = 100000

    def get_instances_from_related(self, related_instance):
        return related_instance.datafile_set.all()

