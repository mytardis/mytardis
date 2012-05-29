from django import template
from django.conf import settings
from django.template.defaultfilters import pluralize, filesizeformat
import pystache

register = template.Library()

def _load_template(template_file):
    from mustachejs.loading import find
    with open(find(template_file), 'r') as f:
        return f.read()

def _mustache_render(tmpl, data):
    from django.utils.safestring import mark_safe
    return mark_safe(pystache.render(tmpl, data))

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
    template = _load_template('tardis_portal/badges/dataset_count')
    count = experiment.datasets.all().count()
    return _mustache_render(template, {
        'title': "%d dataset%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def experiment_datafiles_badge(experiment):
    """
    Displays an badge with the number of datasets for this experiment
    """
    template = _load_template('tardis_portal/badges/datafile_count')
    count = experiment.get_datafiles().count()
    return _mustache_render(template, {
        'title': "%d datafile%s" % (count, pluralize(count)),
        'count': count,
    })

@register.filter
def experiment_public_access_badge(experiment):
    """
    Displays an badge with the number of datasets for this experiment
    """
    template = _load_template('tardis_portal/badges/public_access')
    if experiment.public_access == experiment.PUBLIC_ACCESS_NONE:
        return _mustache_render(template, {
            'title': 'No public access',
            'label': 'Private',
            'private': True,
        })
    if experiment.public_access == experiment.PUBLIC_ACCESS_METADATA:
        return _mustache_render(template, {
            'title': 'Only descriptions are public, not data',
            'label': 'Metadata',
        })
    if experiment.public_access == experiment.PUBLIC_ACCESS_FULL:
        return _mustache_render(template, {
            'title': 'All data is public',
            'label': 'Public',
            'public': True,
        })


@register.filter
def experiment_size_badge(experiment):
    """
    Displays an badge with the number of datasets for this experiment
    """
    template = _load_template('tardis_portal/badges/size')
    size = filesizeformat(experiment.get_size())
    return _mustache_render(template, {
        'title': "Experiment size is ~%s" % size,
        'label': str(size),
    })

