from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.template.defaultfilters import pluralize, filesizeformat
from django.contrib.humanize.templatetags.humanize import naturalday

from tardis.tardis_portal.util import render_mustache
from tardis.tardis_portal.views import get_dataset_info

register = template.Library()

@register.filter
def dataset_tiles(datasets, include_thumbnails):
    # Get data to template (used by JSON service too)
    data = ( get_dataset_info(ds, bool(include_thumbnails)) for ds in datasets )

    class DatasetsInfo(object):
        # Generator which renders a dataset at a time
        def datasets(self):
            for ds in data:
                yield render_mustache('tardis_portal/dataset_tile', ds)

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
def dataset_datafiles_badge(dataset):
    """
    Displays an badge with the number of datafiles for this experiment
    """
    count = dataset.dataset_file_set.count()
    return render_mustache('tardis_portal/badges/datafile_count', {
        'title': "%d file%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def dataset_size_badge(dataset):
    """
    Displays an badge with the total size of the files in this experiment
    """
    size = filesizeformat(dataset.get_size())
    return render_mustache('tardis_portal/badges/size', {
        'title': "Dataset size is ~%s" % size,
        'label': str(size),
    })