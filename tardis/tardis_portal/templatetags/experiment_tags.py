from django import template
from django.conf import settings
from django.template.defaultfilters import pluralize, filesizeformat
from django.contrib.humanize.templatetags.humanize import naturalday
from tardis.tardis_portal.util import get_local_time

from tardis.tardis_portal.util import render_mustache,\
    render_public_access_badge

register = template.Library()

# -----------------------------------------------------------------------------
#   multi_file_upload
# -----------------------------------------------------------------------------
@register.inclusion_tag('tardis_portal/experiment_tags/experiment_browse_item.html')
def experiment_browse_item(experiment, **kwargs):
    """
    Displays an experiment for a browsing view.
    """
    show_images = kwargs.get('can_download') or \
        experiment.public_access == experiment.PUBLIC_ACCESS_FULL
    return {
        'experiment': experiment,
        'show_images': show_images
    }

@register.filter
def experiment_datasets_badge(experiment):
    """
    Displays an badge with the number of datasets for this experiment
    """
    count = experiment.datasets.all().count()
    return render_mustache('tardis_portal/badges/dataset_count', {
        'title': "%d dataset%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def experiment_datafiles_badge(experiment):
    """
    Displays an badge with the number of datafiles for this experiment
    """
    count = experiment.get_datafiles().count()
    return render_mustache('tardis_portal/badges/datafile_count', {
        'title': "%d file%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def experiment_last_updated_badge(experiment):
    return render_mustache('tardis_portal/badges/last_updated_badge', {
        'actual_time': experiment.update_time.strftime('%a %d %b %Y %H:%M'),
        'iso_time': get_local_time(experiment.update_time).isoformat(),
        'natural_time': naturalday(experiment.update_time),
    })

@register.filter
def experiment_public_access_badge(experiment):
    """
    Displays an badge the level of public access for this experiment
    """
    return render_public_access_badge(experiment)


@register.filter
def experiment_size_badge(experiment):
    """
    Displays an badge with the total size of the files in this experiment
    """
    size = filesizeformat(experiment.get_size())
    return render_mustache('tardis_portal/badges/size', {
        'title': "Experiment size is ~%s" % size,
        'label': str(size),
    })

