from lxml.etree import SubElement

from oaipmh.server import NS_XSI

RIFCS_NS = 'http://ands.org.au/standards/rif-cs/registryObjects'
RIFCS_SCHEMA = \
    'http://services.ands.org.au/documentation/rifcs/schema/registryObjects.xsd'

def rifcs_writer(element, metadata):
    map = metadata.getMap()
    # registryObjects
    wrapper = SubElement(element, '{%s}registryObjects' % RIFCS_NS, \
                   nsmap={None: RIFCS_NS, 'xsi': NS_XSI} )
    wrapper.set('{%s}schemaLocation' % NS_XSI,
                '%s %s' % (RIFCS_NS, RIFCS_SCHEMA))
    # registryObject
    obj = SubElement(wrapper, '{%s}registryObject' % RIFCS_NS )
    obj.set('group', map.get('group', ''))
    # key



    #map = metadata.getMap()
    #for name in [
    #    'title', 'creator', 'subject', 'description', 'publisher',
    #    'contributor', 'date', 'type', 'format', 'identifier',
    #    'source', 'language', 'relation', 'coverage', 'rights']:
    #    for value in map.get(name, []):
    #        e = SubElement(e_dc, nsdc(name))
    #        e.text = value