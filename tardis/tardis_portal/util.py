from django.conf import settings

import pystache
import pytz
import os, platform, ctypes, stat, time, struct

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)

def get_local_time(dt):
    '''
    Ensure datetime is timezone-aware and in local time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    '''
    # If datetime is already naive, simply set TZ
    if (dt.tzinfo == None):
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
    if (dt.tzinfo == None):
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
        raise RuntimeError('Unsupported / unexpected platform type: %s' % \
                               sys_type)

def _load_template(template_name):
    from mustachejs.loading import find
    with open(find(template_name), 'r') as f:
        return f.read()

def _mustache_render(tmpl, data):
    from django.utils.safestring import mark_safe
    return mark_safe(pystache.render(tmpl, data))

def render_mustache(template_name, data):
    return _mustache_render(_load_template(template_name), data)
