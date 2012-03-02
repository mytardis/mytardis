from os import path
import pprint

from flexmock import flexmock
from django.test import TestCase
from django.contrib.auth.models import User

from ..site_parser import SiteParser, SiteSettingsParser
import httplib2
from httplib2 import Http


class SiteParserTestCase(TestCase):
    def setUp(self):
        self.sites_filename = path.join(path.dirname(__file__), 'data', 'mytardis_sites.xml')
        self.settings_filename = path.join(path.dirname(__file__), 'data', 'site-settings.xml')
        self.pp = pprint.PrettyPrinter(indent=4)
        self.Http = flexmock()
        flexmock(Http).new_instances(self.Http)

    def testRetrieveSites(self):
        pass

    def testParseSites(self):
        f = open(self.sites_filename)
        parser = SiteParser('')
        l = parser._parse_file(f)
        self.pp.pprint(l)
        self.assertEqual(len(l), 2)

    def testParseSettings(self):
        f = open(self.settings_filename)
        parser = SiteSettingsParser('url')
        d = parser._parse_file(f)
        self.pp.pprint(d)
        self.assertEqual(d['register']['url'], 'http://localhost:8000/experiment/register/')
        self.assertEqual(d['transfer']['type'], 'gridftp')
        self.assertEqual(d['email-endswith'], [ 'email1', 'email2' ])

    def testGetSitesFilename(self):
        parser = SiteParser(self.sites_filename, username='', password='')
        l = parser.get()
        self.pp.pprint(l)
        self.assertEqual(len(l), 2)

    def testGetSitesUrl(self):
        url = 'http://localhost'
        sites_str = open(self.sites_filename).read()
        resp = httplib2.Response({'status': '200'})
        self.Http.should_receive('request').with_args(
                url, 'POST', body=str).and_return((resp, sites_str))

        parser = SiteParser(url, username='', password='')
        l = parser.get()
        self.pp.pprint(l)
        self.assertEqual(len(l), 2)

    def testGetSitesUrlFails(self):
        url = 'http://localhost'
        resp = httplib2.Response({'status': '500'})
        self.Http.should_receive('request').with_args(
                url, 'POST', body=str).and_return((resp, ''))

        parser = SiteParser(url, username='', password='')
        l = parser.get()
        self.assertIsNone(l)

