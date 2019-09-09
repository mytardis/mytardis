'''
Core URLs
'''
from django.conf.urls import url
from django.http import HttpResponse

from tardis.tardis_portal.views import (
    site_settings,
    my_data,
    shared,
    public_data,
    about,
    stats,
    healthz
)

core_urls = [
    url(r'^healthz$', healthz, name='tardis.tardis_portal.views.healthz'),
    url(r'^site-settings.xml/$', site_settings, name='tardis-site-settings'),
    url(r'^mydata/$', my_data, name='tardis.tardis_portal.views.my_data'),
    url(r'^shared/$', shared, name='tardis.tardis_portal.views.shared'),
    url(r'^public_data/', public_data,
        name='tardis.tardis_portal.views.public_data'),
    url(r'^about/$', about, name='tardis.tardis_portal.views.about'),
    url(r'^stats/$', stats, name='tardis.tardis_portal.views.stats'),
    url(r'^robots\.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /download/\nDisallow: /stats/",
        content_type="text/plain"))
]
