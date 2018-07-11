import ctypes
import hashlib
import os
import platform
import warnings

from six.moves import urllib

import pystache
import pytz

from django.conf import settings

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


def get_free_space(fs_dir):
    """ Return free space on the file system holding the given directory
    (in bytes).  This should work on Linux, BSD, Mac OSX and Windows.
    """
    sys_type = platform.system()
    if sys_type == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(fs_dir),
                                                   None, None,
                                                   ctypes.pointer(free_bytes))
        return free_bytes.value
    elif sys_type == 'Darwin' or sys_type == 'DragonFly' or 'BSD' in sys_type:
        st = os.statvfs(fs_dir)
        return st.f_bfree * st.f_frsize
    elif sys_type == 'Linux':
        st = os.statvfs(fs_dir)
        return st.f_bfree * st.f_bsize
    else:
        raise RuntimeError('Unsupported / unexpected platform type: %s' %
                           sys_type)


def generate_file_checksums(sourceFile, tempFile=None, leave_open=False):
    '''DEPRECATED
    Generate checksums, etcetera for a file read from 'sourceFile'.
    If 'tempFile' is provided, the bytes are written to it as they are read.
    The result is a tuple comprising the MD5 checksum, the SHA512 checksum,
    the file length, and chunk containing the start of the file (for doing
    mimetype guessing if necessary).
    '''
    warnings.warn("please replace usages with models/datafile.py:"
                  "compute_checksums", DeprecationWarning)
    sourceFile.seek(0)

    f = sourceFile
    md5 = hashlib.new('md5')
    sha512 = hashlib.new('sha512')
    size = 0
    mimetype_buffer = ''
    for chunk in iter(lambda: f.read(32 * sha512.block_size), ''):
        size += len(chunk)
        if len(mimetype_buffer) < 8096:  # Arbitrary memory limit
            mimetype_buffer += chunk
        md5.update(chunk)
        sha512.update(chunk)
        if tempFile is not None:
            tempFile.write(chunk)
    if leave_open:
        f.seek(0)
    else:
        f.close()
    return (md5.hexdigest(), sha512.hexdigest(),
            size, mimetype_buffer)


def _load_template(template_name):
    from jstemplate.loading import find
    template_locations = find(template_name)
    # Each returned location is a tuple of (template_name, template_path).
    # We'll just use the template_path of the first location
    template_path = template_locations[0][1]
    with open(template_path, 'r') as f:
        return f.read()


def _mustache_render(tmpl, data):
    from django.utils.safestring import mark_safe
    return mark_safe(pystache.render(tmpl, data))


def render_mustache(template_name, data):
    return _mustache_render(_load_template(template_name), data)


def render_public_access_badge(experiment):
    if experiment.public_access == experiment.PUBLIC_ACCESS_NONE and \
            not experiment.is_publication():
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'No public access',
            'label': 'Private',
            'private': True,
        })
    elif experiment.public_access == experiment.PUBLIC_ACCESS_NONE and \
            experiment.is_publication() and \
            not experiment.is_publication_draft():
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'No public access, awaiting approval',
            'label': '[PUBLICATION] Awaiting approval',
            'private': True,
        })
    elif experiment.public_access == experiment.PUBLIC_ACCESS_NONE and \
            experiment.is_publication_draft():
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'No public access',
            'label': '[PUBLICATION] Draft',
            'private': True,
        })

    if experiment.public_access == experiment.PUBLIC_ACCESS_EMBARGO:
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'Under embargo and awaiting release',
            'label': '[PUBLICATION] Awaiting release',
        })
    if experiment.public_access == experiment.PUBLIC_ACCESS_METADATA:
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'Only descriptions are public, not data',
            'label': 'Metadata',
        })
    if experiment.public_access == experiment.PUBLIC_ACCESS_FULL:
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'All data is public',
            'label': 'Public',
            'public': True,
        })
    return None


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

    dataset_filename = urllib.parse.quote(
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

    expt_filename = urllib.parse.quote(
        exp_title, safe=settings.SAFE_FILESYSTEM_CHARACTERS)

    return expt_filename
