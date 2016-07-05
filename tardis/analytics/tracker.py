"""
Generic tracking and analytics interface
Supports Google Analytics through ga.py, others may follow
"""

from tardis.analytics import ga

service = ga
"""This can become a setting to other service in the future"""

track_login = service.track_login
track_logout = service.track_logout
track_download = service.track_download
# sig: label, session_id, ip, user,
# total_size=None, num_files=None,
# ua=None


class IteratorTracker(object):
    """wraps file iterator to track successful and incomplete downloads"""

    def __init__(self, iterator, tracker_data=None):
        self._iterator = iterator
        self.tracker_data = tracker_data
        self.complete = False

    def __iter__(self):
        return self

    def close(self):
        if hasattr(self._iterator, 'close'):
            self._iterator.close()

    def next(self):
        try:
            return self._iterator.next()
        except StopIteration:
            self.complete = True
            raise StopIteration()

    def __del__(self):
        if not self.complete:
            self.tracker_data['label'] = self.tracker_data.get(
                'label', '') + '-aborted'
        track_download(**self.tracker_data)
