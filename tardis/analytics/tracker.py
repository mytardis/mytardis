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
