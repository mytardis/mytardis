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


def get_user_last(user):
    experiments = Experiment.safe.owned_and_shared(user).order_by(
        "-created_time")[:5]
    datasets = Dataset.objects.filter(
        experiments__id__in=map((lambda exp: exp.id), experiments)).order_by(
        "-created_time")[:5]
    instruments = []

    data = {
        "experiments": [],
        "datasets": [],
        "instruments": []
    }

    for experiment in experiments:
        data["experiments"].append({
            "id": experiment.id,
            "title": experiment.title,
            "description": experiment.description,
            "created": experiment.created_time
        })

    for dataset in datasets:
        data["datasets"].append({
            "id": dataset.id,
            "description": dataset.description,
            "created": dataset.created_time
        })
        if dataset.instrument is not None:
            instruments.append({
                "id": dataset.instrument.id,
                "name": dataset.instrument.name
            })

    instruments = {tuple(i.items()) for i in instruments}
    data["instruments"] = [dict(i) for i in instruments]

    return data
