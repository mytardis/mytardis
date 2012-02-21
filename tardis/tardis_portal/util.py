from django.conf import settings

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