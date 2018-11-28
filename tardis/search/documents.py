import logging
import datetime
import elasticsearch_dsl as search

from django.conf import settings

#from haystack import indexes
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from django_elasticsearch_dsl import DocType, Index
from elasticsearch_dsl.connections import connections

from tardis.tardis_portal.models import Dataset, Experiment

logger = logging.getLogger(__name__)


experiment = Index('experiments')

experiment.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@experiment.doc_type
class ExperimentDocument(DocType):
    class Meta:
        model = Experiment

        fields = [
            'title',
            'description',
            'created_time',
            'start_time',
            'end_time',
            'update_time',
            'institution_name',
        ]

