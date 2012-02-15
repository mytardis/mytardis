# -*- coding: utf-8 -*-
from lxml import etree
import urllib
import logging
from StringIO import StringIO

from django.utils.safestring import SafeUnicode


logger = logging.getLogger('tardis.mecat')


class SiteParser:
    """
    class for fetching a list of MyTARDIS sites from a central
    instance or an XML file
    """

    def __init__(self, url, username, password):
	if url.startswith('http'):
	    params = urllib.urlencode({'username': username, 'password': password})
	    import socket
	    socket.setdefaulttimeout(10)
	    f = urllib.urlopen(url, params)
	    if f.getcode() != 200:
		logger.error('SiteParser.__init__ failed with status code %i' % f.getcode())
		logger.error(f.read())
		f.close()
		return
	else:
	    f = open(url)
	self.xmlString = f.read()
	f.close()

        # todo handle errors (incorrect password etc)
        self.tree = etree.parse(StringIO(self.xmlString))
        # logger.debug('Initializing %s' % self.tree)

    def getSingleResult(self, elements):
        if len(elements) == 1:
            return SafeUnicode(elements[0])
        else:
            return None

    def getSiteNames(self):
        return self.tree.xpath("/sites//site/name/text()")

    def getSiteSettingsURL(self, name):
        elements = self.tree.xpath("/sites//site[name='%s']/url/text()" %name)
        return self.getSingleResult(elements)

    def getSiteSettingsUsername(self, name):
        elements = self.tree.xpath("/sites//site[name='%s']/username/text()" %name)
        return self.getSingleResult(elements)

    def getSiteSettingsPassword(self, name):
        elements = self.tree.xpath("/sites//site[name='%s']/password/text()" %name)
        return self.getSingleResult(elements)
