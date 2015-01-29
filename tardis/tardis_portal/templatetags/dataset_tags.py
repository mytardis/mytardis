from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.template.defaultfilters import pluralize, filesizeformat
from django.contrib.humanize.templatetags.humanize import naturalday

from tardis.tardis_portal.util import render_mustache
from tardis.tardis_portal.views import get_dataset_info
from tardis.tardis_portal.models.dataset import Dataset

register = template.Library()


@register.filter
def dataset_tiles(experiment, include_thumbnails):
    # only show 8 datasets for initial load
    datasets = experiment.datasets.all()[:8]

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

        def dataset_verified_size_badge(self):
            if hasattr(self, 'verified_size'):
                return dataset_verified_size_badge(size=self.verified_size)
            ds = Dataset.objects.get(id=self.id)
            return dataset_verified_size_badge(ds)

        def dataset_verified_datafiles_badge(self):
            if hasattr(self, 'verified_datafiles'):
                return dataset_verified_datafiles_badge(count=len(self.verified_datafiles))
            ds = Dataset.objects.get(id=self.id)
            return dataset_verified_datafiles_badge(ds)


    class DatasetsInfo(object):
        # Generator which renders a dataset at a time
        def datasets(self):
            for ds in data:
                yield render_mustache('tardis_portal/dataset_tile',
                                      DatasetInfo(**ds))

    # Render template
    return render_mustache('tardis_portal/dataset_tiles', DatasetsInfo())

@register.filter
def dataset_experiments_badge(dataset):
    """
    Displays an badge with the number of datasets for this experiment
    """
    count = dataset.experiments.all().count()
    return render_mustache('tardis_portal/badges/experiment_count', {
        'title': "In %d experiment%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def dataset_verified_datafiles_badge(dataset=None, count=None):
    """
    Displays an badge with the number of datafiles for this experiment
    """
    if count is None:
        count = len(dataset.get_verified_datafiles())
    return render_mustache('tardis_portal/badges/datafile_count', {
        'title': "%d verified file%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def dataset_verified_size_badge(dataset=None, size=None):
    """
    Displays an badge with the total size of the verified files in this dataset
    """
    if size is None:
        size = filesizeformat(dataset.get_verified_size())
    else:
        size = filesizeformat(size)
    return render_mustache('tardis_portal/badges/size', {
        'title': "Dataset size is ~%s" % size,
        'label': str(size),
    })
