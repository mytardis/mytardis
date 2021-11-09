import logging
import os
import time
import functools
from urllib.parse import quote

from django.conf import settings
from django.db import connection, reset_queries
import pytz


logger = logging.getLogger(__name__)
LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)


def get_local_time(dt):
    '''
    Ensure datetime is timezone-aware and in local time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    '''

    # truncate microseconds
    result = dt.replace(microsecond=0)

    # If datetime is already naive, simply set TZ
    if dt.tzinfo is None:
        result = result.replace(tzinfo=LOCAL_TZ)
    else:
        # Otherwise convert
        result = result.astimezone(LOCAL_TZ)

    return result


def get_utc_time(dt):
    '''
    Ensure datetime is timezone-aware and in UTC time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    '''

    # truncate microseconds
    result = dt.replace(microsecond=0)

    # If datetime is already naive, set TZ
    if dt.tzinfo is None:
        result = result.replace(tzinfo=LOCAL_TZ)

    result = result.astimezone(pytz.utc)
    return result


def _load_template(template_name):
    from jstemplate.loading import find
    template_locations = list(find(template_name))
    # Each returned location is a tuple of (template_name, template_path).
    # We'll just use the template_path of the first location
    template_path = template_locations[0][1]
    with open(template_path, 'r') as f:
        return f.read()


def split_path(p):
    base, top = os.path.split(os.path.normpath(p))
    return (split_path(base) if base and top else []) + [top]


def get_filesystem_safe_dataset_name(dataset):
    """
    Given a Dataset, return a filesystem safe string representing the
    dataset. Useful for filenames for dataset downloads, maybe URLs.

    :param dataset: A Dataset object.
    :type dataset: tardis.tardis_portal.models.dataset.Dataset
    :return: A filesystem safe string as a Dataset name.
    :rtype: basestring
    """
    dataset_filename = dataset.description
    if settings.DATASET_SPACES_TO_UNDERSCORES:
        dataset_filename = dataset_filename.replace(' ', '_')

    dataset_filename = quote(
        dataset_filename,
        safe=settings.SAFE_FILESYSTEM_CHARACTERS)

    return dataset_filename


def get_filesystem_safe_experiment_name(experiment):
    """
    Given an Experiment, return a filesystem safe string representing the
    experiment. Useful for filenames for experiment downloads, maybe URLs.

    :param experiment: A Experiment object.
    :type experiment: tardis.tardis_portal.models.experiment.Experiment
    :return: A filesystem safe string as a Experiment name.
    :rtype: basestring
    """
    exp_title = experiment.title
    if settings.EXP_SPACES_TO_UNDERSCORES:
        exp_title = exp_title.replace(' ', '_')

    expt_filename = quote(
        exp_title, safe=settings.SAFE_FILESYSTEM_CHARACTERS)

    return expt_filename


def query_debugger(func):

    @functools.wraps(func)
    def inner_func(*args, **kwargs):

        reset_queries()
        start_queries = len(connection.queries)
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        end_queries = len(connection.queries)

        logger.info(f"Function : {func.__name__}")
        logger.info(f"Number of Queries : {end_queries - start_queries}")
        logger.info(f"Finished in : {(end - start):.2f}s")

        return result

    return inner_func
