from django.conf import settings

from .site_parser import SiteParser, SiteSettingsParser


class SiteManager(object):
    def __init__(self, url=settings.MYTARDIS_SITES_URL):
        self.url = url
        try:
            self.username = settings.MYTARDIS_SITES_USERNAME
            self.password = settings.MYTARDIS_SITES_PASSWORD
        except AttributeError:
            self.username = ''
            self.password = ''
        self.site_parser = SiteParser(self.url, username=self.username, password=self.password)

    def sites(self):
        sites = self.site_parser.get()
        if sites is None:
            return
        for site in sites:
            ssp = SiteSettingsParser(
                    site['url'], username=site['username'], password=site['password'])
            site_settings = ssp.get()
            if site_settings is not None:
                yield site_settings

    def get_site_settings(self, url):
        sites = self.site_parser.get()
        if sites is None:
            return None
        for site in sites:
            if site['url'] == url:
                ssp = SiteSettingsParser(
                        site['url'], username=site['username'], password=site['password'])
                if ssp is not None:
                    return ssp.get()
                return None
        return None
