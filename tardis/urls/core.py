'''
Core URLs
'''
from django.conf.urls import url
from django.http import HttpResponse

from tardis.tardis_portal.views import (
    site_settings,
    my_data,
    public_data,
    about,
    stats,
    cybderduck_connection_window,
    sftp_access
)

core_urls = [
    url(r'^site-settings.xml/$', site_settings, name='tardis-site-settings'),
    url(r'^mydata/$', my_data, name='tardis.tardis_portal.views.my_data'),
    url(r'^public_data/', public_data,
        name='tardis.tardis_portal.views.public_data'),
    url(r'^about/$', about, name='tardis.tardis_portal.views.about'),
    url(r'^stats/$', stats, name='tardis.tardis_portal.views.stats'),
    url(r'^sftp_access/cyberduck/connection.png$',
        cybderduck_connection_window, name='cyberduck_connection_window'),
    url(r'^sftp_access/$', sftp_access,
        name='tardis.tardis_portal.views.sftp_access'),
    url(r'^robots\.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /download/\nDisallow: /stats/",
        content_type="text/plain"))
]
