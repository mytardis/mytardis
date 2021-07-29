from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFile


def get_user_stats(user):
    experiments = Experiment.safe.owned_and_shared(user)
    datasets = Dataset.objects.filter(
        experiments__id__in=map((lambda exp: exp.id), experiments))
    datafiles = DataFile.objects.filter(
        dataset__id__in=map((lambda ds: ds.id), datasets))
    return {
        "experiments": len(experiments),
        "datasets": len(datasets),
        "datafiles": len(datafiles),
        "size": sum(map((lambda df: df.size), datafiles))
    }
