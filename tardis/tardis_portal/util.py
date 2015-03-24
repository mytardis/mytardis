from django.conf import settings

import ctypes
import hashlib
import os
import platform
import pystache
import pytz

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)


def get_local_time(dt):
    '''
    Ensure datetime is timezone-aware and in local time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    '''
    # If datetime is already naive, simply set TZ
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TZ)
    # Otherwise convert
    return dt.astimezone(LOCAL_TZ)


def get_utc_time(dt):
    '''
    Ensure datetime is timezone-aware and in UTC time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    '''
    # If datetime is already naive, set TZ
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt.astimezone(pytz.utc)


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
    '''
    Generate checksums, etcetera for a file read from 'sourceFile'.
    If 'tempFile' is provided, the bytes are written to it as they are read.
    The result is a tuple comprising the MD5 checksum, the SHA512 checksum,
    the file length, and chunk containing the start of the file (for doing
    mimetype guessing if necessary).
    '''
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
    from mustachejs.loading import find
    with open(find(template_name), 'r') as f:
        return f.read()


def _mustache_render(tmpl, data):
    from django.utils.safestring import mark_safe
    return mark_safe(pystache.render(tmpl, data))


def render_mustache(template_name, data):
    return _mustache_render(_load_template(template_name), data)


def render_public_access_badge(experiment):
    if experiment.public_access == experiment.PUBLIC_ACCESS_NONE and\
       not experiment.is_publication():
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'No public access',
            'label': 'Private',
            'private': True,
        })
    elif experiment.public_access == experiment.PUBLIC_ACCESS_NONE and\
       experiment.is_publication() and not experiment.is_publication_draft():
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'No public access, awaiting approval',
            'label': '[PUBLICATION] Awaiting approval',
            'private': True,
        })
    elif experiment.public_access == experiment.PUBLIC_ACCESS_NONE and\
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
