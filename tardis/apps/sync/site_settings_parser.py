# -*- coding: utf-8 -*-

import logging
from lxml import etree
from StringIO import StringIO
import urllib

from django.utils.safestring import SafeUnicode


logger = logging.getLogger('tardis.mecat')


class SiteSettingsParser:
    def __init__(self, url, username, password):

	params = urllib.urlencode({'username': username, 'password': password})
	import socket
	socket.setdefaulttimeout(10)
	f = urllib.urlopen(url, params)
	if f.getcode() != 200:
	    logger.error('SiteSettingsParser.__init__ failed with status code %i' % f.getcode())
	    # logger.error(f.read())
	    f.close()
	    return
	self.xmlString = f.read()
	f.close()
        self.tree = etree.parse(StringIO(self.xmlString))
        # logger.debug('Initializing %s' % self.tree)

    def getSingleResult(self, elements):
        if len(elements) == 1:
            return SafeUnicode(elements[0])
        else:
            return None

    def getEmailEndswith(self):
        return self.tree.xpath("/site-settings/email-endswith/text()")

    def getTransferSetting(self, name):
        elements = self.tree.xpath("/site-settings/transfer/%s/text()" % name)
        return self.getSingleResult(elements)

    def getRegisterSetting(self, name):
        elements = self.tree.xpath("/site-settings/register/%s/text()" % name)
        return self.getSingleResult(elements)
