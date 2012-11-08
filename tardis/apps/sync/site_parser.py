# -*- coding: utf-8 -*-
from lxml import etree
from lxml.etree import XMLSyntaxError
import urllib
import logging
from StringIO import StringIO
from httplib2 import Http

from django.utils.safestring import SafeUnicode


logger = logging.getLogger('tardis.mecat')


class URLParser(object):

    def __new__(cls, *args, **kwargs):
        return super(URLParser, cls).__new__(cls)

    def __init__(self, url, **creds):
        self.url = url
        self.creds = creds
        self.result = None

    def get(self):
        f = self._open_file(self.url, **self.creds)
        if f:
            result = self._parse_file(f)
            f.close()
            return result
        return None

    def _open_file(self, url, username, password):
        if self.url.startswith('http'):
            # This should pull in and use HttpClient or at least httplib2.
            body = urllib.urlencode({'username': username, 'password': password})

            h = Http(timeout=10, disable_ssl_certificate_validation=True)
            h.force_exception_to_status_code = True
            resp, content = h.request(url, 'POST', body=body)
            if resp.status != 200:
                logger.error('URLParser: POST for url %s failed: %s %s' % (url, resp.status, resp.reason))
                return None
            f = StringIO(content)
        else:
            try:
                f = open(url)
            except IOError:
                logger.error('URLParser: File %s does not exist' % (url))
                return None
        return f

    def _parse_file(self, f):
        return NotImplementedError()


class SiteParser(URLParser):

    def __new__(cls, *args, **kwargs):
        return super(URLParser, cls).__new__(cls)

    def _parse_file(self, f):
        """Build a list of dictionaries from the sites file."""
        tree = etree.iterparse(f, events=('start', 'end'))
        sites = []
        site = None
        seen_sites_end = False
        try:
            for event, element in tree:
                # print event, element.tag, element.text
                if element.tag == 'sites' and event == 'end':
                    seen_sites_end = True
                elif element.tag == 'site':
                    if event == 'start':
                        site = {}
                        sites.append(site)
                    if event == 'end':
                        site = None
                elif site is not None:
                    site[element.tag] = SafeUnicode(element.text)
        except XMLSyntaxError as e:
            # Workaround for a spurious "internal error" exception
            # that is thrown after parsing the closing 'sites' tag
            if not seen_sites_end:
                raise e
        return sites


class SiteSettingsParser(URLParser):

    def __new__(cls, *args, **kwargs):
        return super(URLParser, cls).__new__(cls)

    def _parse_file(self, f):
        """Build nested dicts to mirror the XML format of the settings file."""
        tree = etree.iterparse(f, events=('start', 'end'))
        settings = {}
        current_level = settings
        seen_site_settings_end = False
        try: 
            for event, element in tree:
                # print event, element.tag, element.text
                if event == 'end' and element.tag == 'site-settings':
                    seen_site_settings_end = True
                text = SafeUnicode(element.text).strip()
                if not text:
                    if event == 'start':
                        # Add a nested dict, saving the parent.
                        current_level[element.tag] = {
                            '_parent': current_level }
                        current_level = current_level[element.tag]
                    elif event == 'end':
                        # Un-nest back to the parent level.
                        parent = current_level['_parent']
                        del current_level['_parent']
                        current_level = parent
                elif event == 'start':
                    if element.tag in current_level:
                        if not isinstance(current_level[element.tag], list):
                            current_level[element.tag] = [ 
                                current_level[element.tag] ]
                        current_level[element.tag].append(text)
                    else:
                        current_level[element.tag] = text
        except XMLSyntaxError as e:
            # Workaround for a spurious "internal error" exception
            # that is thrown after parsing the closing 'site-settings' tag
            if not seen_site_settings_end:
                raise e

        # Fix for email-ends-with
        s = settings['site-settings']
        if not isinstance(s['email-endswith'], list):
            s['email-endswith'] = [ s['email-endswith'] ]
        return s
