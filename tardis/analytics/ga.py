"""
Google analyitics tracking
"""

import logging
import random
import requests

from django.conf import settings

GA_ID = getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
GA_USER_TRACKING = getattr(settings, 'GOOGLE_ANALYTICS_USER_TRACKING', False)

logger = logging.getLogger(__name__)


def _track_event(payload, cid=None, uid=None):
    """
    example_payload = {
        't': 'event',
        'ec': 'category',
        'ea': 'action',
        'el': 'label',
        'ev': 1,
    }

    :param payload:
    :param uid:
    :return:

    """
    if GA_ID is None:
        return

    data = {
        'v': '1',
        'tid': GA_ID,
        'cid': cid or random.randint(1, 1000)
    }
    if GA_USER_TRACKING and uid is not None:
        data.update({
            'uid': uid,
        })
    data.update(payload)

    try:
        response = requests.post(
            'http://www.google-analytics.com/collect', data=data)
        response.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError) as e:
        logger.debug('Google analytics error: %s, payload: %s' % (e, data))


def track_login(label, session_id, ip, user):
    _track_event({
        't': 'event',
        'sc': 'start',
        'cid': session_id,
        'uip': ip,
        'ec': 'auth',
        'ea': 'login',
        'el': label,
    },
        uid=user.id)


def track_logout(label, session_id, ip, user):
    _track_event({
        't': 'event',
        'sc': 'end',
        'cid': session_id,
        'uip': ip,
        'ec': 'auth',
        'ea': 'logout',
        'el': label,
    },
        uid=user.id)
