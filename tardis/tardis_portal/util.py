from django.conf import settings

import pytz

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)

def get_local_time(dt):
    '''
    Ensure datetime is timezone-aware and in local time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    (SteveB: that comment dates from a previous version of this function - I don't
    know if it's still true.)
    '''
    # If datetime is already  naive, simply set TZ
    if (dt.tzinfo == None):
        return LOCAL_TZ.localize(dt)
    # Otherwise convert
    return LOCAL_TZ.normalize(dt.astimezone(LOCAL_TZ))

def get_local_time_naive(dt):
    '''
    Ensure datetime is timezone-naive and in local time.
    '''
    return get_local_time(dt).replace(tzinfo=None)

def get_utc_time(dt):
    '''
    Ensure datetime is timezone-aware and in UTC time.

    If the USE_TZ setting in the current dev version of Django comes in,
    this *should* keep providing correct behaviour.
    '''
    # If datetime is already naive, set TZ
    
    if (dt.tzinfo == None):
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return pytz.utc.normalize(dt.astimezone(pytz.utc))
