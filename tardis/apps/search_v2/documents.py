import logging

from django_elasticsearch_dsl import DocType, Index, fields

from tardis.tardis_portal.models import Dataset, Experiment, DataFile

logger = logging.getLogger(__name__)


experiment = Index('experiments')

experiment.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@experiment.doc_type
class ExperimentDocument(DocType):

    id = fields.IntegerField()
    title = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    description = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    created_time = fields.DateField()
    start_time = fields.DateField()
    end_time = fields.DateField()
    created_time = fields.DateField()
    update_time = fields.DateField()
    institution_name = fields.StringField()

    class Meta:
        model = Experiment


dataset = Index('dataset')

dataset.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@dataset.doc_type
class DatasetDocument(DocType):
    id = fields.IntegerField()
    description = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    experiments = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'title': fields.TextField(
            fields={'raw': fields.KeywordField()
                    }
        )
    }
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()

    class Meta:
        model = Dataset
        related_models = [Experiment]
    """
    def get_queryset(self):
        return super(DatasetDocument, self).get_queryset().select_related(
            'experiments'
        )
    """
    def get_instances_from_related(self, related_instance):
            return related_instance.datasets.all()


datafile = Index('datafile')

datafile.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@datafile.doc_type
class DataFileDocument(DocType):
    filename = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    created_time = fields.DateField()
    modification_time = fields.DateField()

    class Meta:
        model = DataFile
