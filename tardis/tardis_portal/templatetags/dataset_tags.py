from django import template
from django.template.defaultfilters import pluralize, filesizeformat

from ..util import render_mustache
from ..views import get_dataset_info
from ..models.dataset import Dataset
from ..models.experiment import Experiment

register = template.Library()


@register.simple_tag
def dataset_tiles(experiment_id, user, include_thumbnails):
    # only show 8 datasets for initial load
    datasets = Dataset.safe.all(user).filter(experiments__id=experiment_id
                                             ).order_by('description')[:8]

    # Get data to template (used by JSON service too)
    # ?? doesn't seem to be used by JSON service at all
    data = (get_dataset_info(ds, bool(include_thumbnails),
                             exclude=['datasettype', 'size'])
            for ds in datasets)

    class DatasetInfo(object):

        def __init__(self, **data):
            self.__dict__.update(data)

        def experiment_badge(self):
            count = len(self.experiments)
            return render_mustache('tardis_portal/badges/experiment_count', {
                'title': "In %d experiment%s" % (count, pluralize(count)),
                'count': count,
            })

        def dataset_size_badge(self):
            if hasattr(self, 'size'):
                return dataset_size_badge(size=self.size)
            ds = Dataset.objects.get(id=self.id)
            return dataset_size_badge(ds)

        def dataset_datafiles_badge(self):
            if hasattr(self, 'datafiles'):
                return dataset_datafiles_badge(count=len(self.datafiles))
            ds = Dataset.objects.get(id=self.id)
            return dataset_datafiles_badge(ds)

    class DatasetsInfo(object):
        # Generator which renders a dataset at a time
        def datasets(self):
            for ds in data:
                yield render_mustache('tardis_portal/dataset_tile',
                                      DatasetInfo(**ds))

    # Render template
    return render_mustache('tardis_portal/dataset_tiles', DatasetsInfo())


@register.simple_tag
def dataset_experiments_badge(dataset, user):
    """
    Displays a badge with the number of experiments for this dataset
    """
    count = Experiment.safe.all(user).filter(dataset__id=dataset.id
                                             ).count()
    return render_mustache('tardis_portal/badges/experiment_count', {
        'title': "In %d experiment%s" % (count, pluralize(count)),
        'count': count,
    })


@register.filter
def dataset_datafiles_badge(dataset=None, count=None):
    """
    Displays an badge with the number of datafiles for this experiment
    """
    if count is None:
        count = dataset.datafile_set.count()
    return render_mustache('tardis_portal/badges/datafile_count', {
        'title': "%d file%s" % (count, pluralize(count)),
        'count': count,
    })


@register.filter
def dataset_size_badge(dataset=None, size=None):
    """
    Displays an badge with the total size of the files in this experiment
    """
    if size is None:
        size = filesizeformat(dataset.get_size())
    else:
        size = filesizeformat(size)
    return render_mustache('tardis_portal/badges/size', {
        'title': "Dataset size is ~%s" % size,
        'label': size,
    })
