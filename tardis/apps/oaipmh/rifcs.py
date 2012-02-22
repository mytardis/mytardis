from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from lxml.etree import SubElement

from oaipmh.server import NS_XSI

RIFCS_NS = 'http://ands.org.au/standards/rif-cs/registryObjects'
RIFCS_SCHEMA = \
    'http://services.ands.org.au/documentation/rifcs/schema/registryObjects.xsd'

def rifcs_writer(element, metadata):
    # registryObjects
    wrapper = SubElement(element, _nsrif('registryObjects'), \
                   nsmap={None: RIFCS_NS, 'xsi': NS_XSI} )
    wrapper.set('{%s}schemaLocation' % NS_XSI,
                '%s %s' % (RIFCS_NS, RIFCS_SCHEMA))
    # registryObject
    obj = SubElement(wrapper, _nsrif('registryObject') )
    obj.set('group', _get_group(metadata))
    # key
    SubElement(obj, _nsrif('key')).text = _get_id(metadata)
    # originatingSource
    SubElement(obj, _nsrif('originatingSource')).text = \
        _get_originating_source(metadata)
    # collection
    collection = SubElement(obj, _nsrif('collection') )
    collection.set('type', 'dataset')
    # name
    name = SubElement(collection, _nsrif('name') )
    name.set('type', 'primary')
    SubElement(name, _nsrif('namePart')).text = metadata.getMap().get('title')
    # description
    description = SubElement(collection, _nsrif('description') )
    description.set('type', 'brief')
    description.text = metadata.getMap().get('description')
    # location
    electronic = SubElement(SubElement(SubElement(collection,
                                                  _nsrif('location') ),
                                       _nsrif('address')),
                            _nsrif('electronic'))
    electronic.set('type', 'url')
    electronic.text = _get_location(metadata)

    #map = metadata.getMap()
    #for name in [
    #    'title', 'creator', 'subject', 'description', 'publisher',
    #    'contributor', 'date', 'type', 'format', 'identifier',
    #    'source', 'language', 'relation', 'coverage', 'rights']:
    #    for value in map.get(name, []):
    #        e = SubElement(e_dc, nsdc(name))
    #        e.text = value

def _nsrif(name):
    return '{%s}%s' % (RIFCS_NS, name)

def _get_id(metadata):
    return "%s/experiment/%s" % \
        (Site.objects.get_current().domain, metadata.getMap().get('id'))

def _get_group(metadata):
    return metadata.getMap().get('group', getattr(settings, 'RIFCS_GROUP', ''))

def _get_originating_source(metadata):
    # TODO: Handle repository data from federated MyTardis instances
    return "http://%s/" % Site.objects.get_current().domain

def _get_location(metadata):
    # TODO: Handle repository data from federated MyTardis instances
    return "http://%s%s" % \
        ( Site.objects.get_current().domain,
          reverse('experiment', args=[metadata.getMap().get('id')]) )