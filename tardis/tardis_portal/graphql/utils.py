import graphene

from django.db.models import Q

from ..models.experiment import Experiment
from ..models.datafile import DataFile

class ExtendedConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()
    edge_count = graphene.Int()

    def resolve_total_count(self, info, **kwargs):
        return self.length

    def resolve_edge_count(self, info, **kwargs):
        return len(self.edges)


def get_accessible_experiments(user):
    return Experiment.safe.all(user)


def get_accessible_datafiles(user):
    experiments = get_accessible_experiments(user)
    if experiments.count() == 0:
        return DataFile.objects.none()

    queries = [Q(dataset__experiments__id=id)
        for id in experiments.values_list('id', flat=True)]

    query = queries.pop()
    for item in queries:
        query |= item

    return DataFile.objects.filter(query)
