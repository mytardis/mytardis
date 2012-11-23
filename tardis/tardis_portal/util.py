from django.conf import settings

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
    if experiment.public_access == experiment.PUBLIC_ACCESS_NONE:
        return render_mustache('tardis_portal/badges/public_access', {
            'title': 'No public access',
            'label': 'Private',
            'private': True,
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