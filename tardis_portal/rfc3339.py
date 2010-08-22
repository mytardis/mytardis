#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
The function `rfc3339` formats dates according to the :RFC:`3339`. `rfc3339`
tries to have as much as possible sensible defaults.
'''

__author__ = 'Henry Precheur <henry@precheur.org>'
__license__ = 'Public Domain'
__all__ = ('rfc3339', )

import datetime
import time


def _timezone(utcoffset):
    '''
    Return a string reprenseting the timezone offset.

    >>> _timezone(3600)
    '+01:00'
    >>> _timezone(-28800)
    '-08:00'
    '''

    hours = abs(utcoffset) // 3600
    minutes = abs(utcoffset) % 3600
    if utcoffset >= 0:
        return '+%02d:%02d' % (hours, minutes)
    else:
        return '-%02d:%02d' % (hours, minutes)


def _utc_offset(date, use_system_timezone):
    '''
    Return the UTC offset of `date`. If `date` does not have any `tzinfo`, use
    the timezone informations stored locally on the system.

    >>> if time.daylight:
    ...     system_timezone = -time.altzone
    ... else:
    ...     system_timezone = -time.timezone
    >>> _utc_offset(datetime.datetime.now(), True) == system_timezone
    True
    >>> _utc_offset(datetime.datetime.now(), False)
    0
    '''

    if date.utcoffset() is not None:
        return date.utcoffset()
    elif use_system_timezone:
        if time.daylight:
            return -time.altzone
        else:
            return -time.timezone
    else:
        return 0


def _utc_string(d):
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')


def rfc3339(date, utc=False, use_system_timezone=True):
    '''
    Return a string formatted according to the :RFC:`3339`. If called with
    `utc=True`, it normalizes `date` to the UTC date. If `date` does not have
    any timezone information, uses the local timezone::

        >>> date = datetime.datetime(2008, 4, 2, 20)
        >>> rfc3339(date, utc=True, use_system_timezone=False)
        '2008-04-02T20:00:00Z'
        >>> rfc3339(date) # doctest: +ELLIPSIS
        '2008-04-02T20:00:00...'

    If called with `user_system_time=False` don't use the local timezone and
    consider the offset to UTC to be zero::

        >>> rfc3339(date, use_system_timezone=False)
        '2008-04-02T20:00:00+00:00'

    `date` must be a a `datetime.datetime`, `datetime.date` or a timestamp as
    returned by `time.time()`::

        >>> rfc3339(0, utc=True, use_system_timezone=False)
        '1970-01-01T00:00:00Z'
        >>> rfc3339(datetime.date(2008, 9, 6), use_system_timezone=False)
        '2008-09-06T00:00:00+00:00'
        >>> rfc3339('foo bar')
        Traceback (most recent call last):
        ...
        TypeError: excepted datetime, got str instead
    '''

    # Check if `date` is a timestamp.

    try:
        if utc:
            return _utc_string(datetime.datetime.utcfromtimestamp(date))
        else:
            date = datetime.datetime.fromtimestamp(date)
    except TypeError:
        pass
    if isinstance(date, datetime.date):

        # If `date` is a `datetime.date` convert it to a `datetime.datetime`.

        if not isinstance(date, datetime.datetime):
            date = datetime.datetime(*date.timetuple()[:3])
        utcoffset = _utc_offset(date, use_system_timezone)
        if utc:
            return _utc_string(date
                               + datetime.timedelta(seconds=utcoffset))
        else:
            return date.strftime('%Y-%m-%dT%H:%M:%S') \
                + _timezone(utcoffset)
    else:
        raise TypeError('excepted %s, got %s instead'
                        % (datetime.datetime.__name__,
                        date.__class__.__name__))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
