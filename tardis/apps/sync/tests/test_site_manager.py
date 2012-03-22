from os import path
import pprint

from flexmock import flexmock
from django.test import TestCase
from django.contrib.auth.models import User

from ..site_manager import SiteManager
from ..site_parser import SiteParser, SiteSettingsParser


class SiteManagerTestCase(TestCase):
    def setUp(self):
        self.sites_filename = path.join(path.dirname(__file__), 'data', 'mytardis_sites.xml')
        self.sp = flexmock()
        flexmock(SiteParser).new_instances(self.sp)
        self.sites = [
                { 'url': 'testurl', 'name': 'testname', 'username': 'testuser', 'password': 'testpw' },
                { 'url': 'testurl2', 'name': 'testname2', 'username': 'testuser2', 'password': 'testpw2' },
        ]
        self.site_settings = { 'setting1': 'setting1text', 'setting2': 'setting2text' }

    def testGetSites(self):
        self.sp.should_receive('get').and_return(self.sites)

        sm = SiteManager()
        for i, site in enumerate(sm.sites()):
            for key in sites[i]:
                self.assertEqual(site[key], self.sites[i][key])

    def testGetNoSites(self):
        self.sp.should_receive('get').and_return([])

        sm = SiteManager()
        for site in sm.sites():
            self.fail()

    def testGetSiteSettings(self):
        self.sp.should_receive('get').and_return(self.sites)
        self.ssp = flexmock()
        flexmock(SiteSettingsParser).new_instances(self.ssp)
        self.ssp.should_receive('get').and_return(self.site_settings)

        sm = SiteManager()
        result = sm.get_site_settings(self.sites[0]['url'])
        for key in self.site_settings:
            self.assertEqual(result[key], self.site_settings[key])

    def testGetSiteSettingsFail(self):
        self.sp.should_receive('get').and_return(self.sites)
        self.ssp = flexmock()
        flexmock(SiteSettingsParser).new_instances(self.ssp)
        self.ssp.should_receive('get').and_return(None)

        sm = SiteManager()
        result = sm.get_site_settings(self.sites[0]['url'])
        self.assertEqual(None, result)
