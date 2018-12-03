import logging

from django_elasticsearch_dsl import DocType, Index, fields

from tardis.tardis_portal.models import Dataset, Experiment

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

    description = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )
    created_time = fields.DateField()
    modified_time = fields.DateField()

    class Meta:
        model = Dataset
