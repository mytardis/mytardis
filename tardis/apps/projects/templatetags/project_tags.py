# from datetime import datetime
from django import template

# from django.template.defaultfilters import pluralize
# from django.contrib.humanize.templatetags.humanize import naturalday
# from ..util import get_local_time

# from ..util import render_public_access_badge
from tardis.tardis_portal.models.experiment import Experiment

# from ..models.access_control import ExperimentACL, DatafileACL, DatasetACL

register = template.Library()
# def get_all_project_experiments(project_id, user):
#    """
#    Returns all experiment objects in a project.
#    """
#    return Experiment.safe.all(user).filter(project__id=project_id)
@register.simple_tag
def project_get_recent_experiments(project_id, user):
    """
    Return the 5 most recently updated experiments for this project
    """
    experiments = (
        Experiment.safe.all(user)
        .filter(project__id=project_id)
        .order_by("-update_time")[:4]
    )
    return experiments


'''
@register.simple_tag
def project_experiments_badge(project_id, user):
    """
    Displays a badge with the number of experiments for this project.
    """
    # count = Experiment.safe.all(user).filter(project__id=project_id).count()
    if not user.is_authenticated:
        from ..auth.token_auth import TokenGroupProvider

        tgp = TokenGroupProvider()
        query = ExperimentACL.objects.none()
        for token in tgp.getGroups(user):
            query |= (
                token.experimentacls.select_related("experiment")
                .prefetch_related("experiment__project")
                .filter(experiment__project__id=project_id)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("experiment__id")
            )
    else:
        query = (
            user.experimentacls.select_related("experiment")
            .prefetch_related("experiment__project")
            .filter(experiment__project__id=project_id)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("experiment__id")
        )
        for group in user.groups.all():
            query |= (
                group.experimentacls.select_related("experiment")
                .prefetch_related("experiment__project")
                .filter(experiment__project__id=project_id)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("experiment__id")
            )
    count = query.distinct().count()
    return render_mustache(
        "tardis_portal/badges/experiment_count",
        {
            "title": "%d experiment%s" % (count, pluralize(count)),
            "count": count,
        },
    )
'''

'''@register.simple_tag
def project_datafiles_badge(project, user):
    """
    Displays a badge with the number of datafiles for this project.
    """
    # count = project.get_datafiles(user).count()
    if not user.is_authenticated:
        from ..auth.token_auth import TokenGroupProvider

        tgp = TokenGroupProvider()
        query = DatafileACL.objects.none()
        for token in tgp.getGroups(user):
            query |= (
                token.datafileacls.select_related("datafile")
                .prefetch_related("datafile__dataset__experiments__project")
                .filter(datafile__dataset__experiments__project__id=project.id)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("datafile__id")
            )
    else:
        query = (
            user.datafileacls.select_related("datafile")
            .prefetch_related("datafile__dataset__experiments__project")
            .filter(datafile__dataset__experiments__project__id=project.id)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("datafile__id")
        )
        for group in user.groups.all():
            query |= (
                group.datafileacls.select_related("datafile")
                .prefetch_related("datafile__dataset__experiments__project")
                .filter(datafile__dataset__experiments__project__id=project.id)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("datafile__id")
            )
    count = query.distinct().count()
    return render_mustache(
        "tardis_portal/badges/datafile_count",
        {
            "title": "%d file%s" % (count, pluralize(count)),
            "count": count,
        },
    )
'''

'''@register.simple_tag
def project_datasets_badge(project_id, user):
    """
    Displays a badge with the number of datasets for this project
    """
    if not user.is_authenticated:
        from ..auth.token_auth import TokenGroupProvider

        tgp = TokenGroupProvider()
        query = DatasetACL.objects.none()
        for token in tgp.getGroups(user):
            query |= (
                token.datasetacls.select_related("dataset")
                .prefetch_related("dataset__experiments__project")
                .filter(dataset__experiments__project__id=project_id)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("dataset__id")
            )
    else:
        query = (
            user.datasetacls.select_related("dataset")
            .prefetch_related("dataset__experiments__project")
            .filter(dataset__experiments__project__id=project_id)
            .exclude(
                effectiveDate__gte=datetime.today(), expiryDate__lte=datetime.today()
            )
            .values_list("dataset__id")
        )
        for group in user.groups.all():
            query |= (
                group.datasetacls.select_related("dataset")
                .prefetch_related("dataset__experiments__project")
                .filter(dataset__experiments__project__id=project_id)
                .exclude(
                    effectiveDate__gte=datetime.today(),
                    expiryDate__lte=datetime.today(),
                )
                .values_list("dataset__id")
            )
    count = query.distinct().count()
    return render_mustache(
        "tardis_portal/badges/dataset_count",
        {
            "title": "%d dataset%s" % (count, pluralize(count)),
            "count": count,
        },
    )
'''

"""
@register.filter
def project_last_updated_badge(project):
    return render_mustache(
        "tardis_portal/badges/last_updated_badge",
        {
            "actual_time": get_local_time(project.start_time).strftime(
                "%a %d %b %Y %H:%M"
            ),
            "iso_time": get_local_time(project.start_time).isoformat(),
            "natural_time": naturalday(project.start_time),
        },
    )
"""


# @register.filter
# def project_public_access_badge(project):
#    """
#    Displays a badge the level of public access for this experiment
#    """
# return render_public_access_badge(project)


# @register.inclusion_tag("templatetags/project_tags/project_badges.html")
# def project_badges(project, user, **kwargs):
#    """
#    Displays badges for a Project for displaying in an Project list view
#    """
#    return {"project": project, "user": user}


# @register.inclusion_tag("projects/templatetags/project_tags/project_download_link.html")
# def project_download_link(project, **kwargs):
#    """
#    Displays a download link for a project in a list view
#    """
#    return {"project": project}
