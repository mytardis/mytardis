from django import template

register = template.Library()


@register.inclusion_tag("tardis_portal/experiment_tags/experiment_authors.html")
def experiment_authors(experiment, **kwargs):
    """
    Displays an experiment's authors in an experiment list view
    """
    return {"experiment": experiment}


@register.inclusion_tag("tardis_portal/experiment_tags/experiment_download_link.html")
def experiment_download_link(experiment, **kwargs):
    """
    Displays a download link for an experiment in a list view
    """
    return {"experiment": experiment}
