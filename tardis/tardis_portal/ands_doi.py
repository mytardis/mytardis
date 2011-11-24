""" ands_doi.py """

from django.conf import settings
from urllib2 import HTTPError
from urllib import urlencode  # no urlencode in urllib2

import urllib2

import logging
logger = logging.getLogger(__name__)


class DOIService(object):
    """
    DOIService

    Mints DOIs using ANDS' Cite My Data service
    POSTs DataCite XML to a web services endpoint
    """

    def __init__(self, experiment):
        """
        :param experiment: The experiment model object
        :type experiment: :class: `tardis.tardis_portal.models.Experiment`
        """
        if hasattr(settings, 'DOI_ENABLED') and settings.DOI_ENABLED:
            self.experiment = experiment

            provider = settings.DOI_XML_PROVIDER
            module, constructor = provider.rsplit('.', 1)

            module = __import__(module)
            constructor = getattr(module, constructor)

            self.doi_provider = constructor(experiment)  # FIXME

            self.schema = Schema.objects.get(namespace=settings.DOI_NAMESPACE)

        else:
            raise Exception('DOI is not enabled')

    def get_or_mint_doi(self, url):
        """
            :param url: the URL the DOI will resolve to
            :type url: string
            :return: the DOI string
            :rtype string
        """
        doi = self.get_doi()
        if doi:
            return doi
        else:
            try:
                return self._mint_doi(url)
            except HTTPError:
                logger.exception('mint doi failed')
                raise

    def get_doi(self):
        """ return DOI or None"""
        .objects.filter(schema=self.schema, experiment=self.experiment)
        doi_params = ExperimentParameter.objects.get(parameterset__schema=self.schema, parameterset__experiment=self.experiment, name__name='doi')  #TODO un-hardcode
        if doi_params.count() == 1 
            return doi_params[0].string_value
        return None


    def _mint(self, url):
        xml = self._datacite_xml()
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        post_data = urlencode({
            'xml': xml
        })

        req = urllib2.Request(mint_url, post_data, headers)
        resp = urllib2.urlopen(req)

        data = response.read()

        paramset = self._get_or_create_doi_parameterset()
        ep = ExperimentParameter(parameterset=paramset, name='doi', string_value=data)
        ep.save()

        return data

    def _datacite_xml(self):
        return self.doi_provider.xml(experiment)
        

class DOIXMLProvider(object):
    def __init__(self, experiment):
        self.experiment = experiment

    def xml(self):
        from django.template import Context
        c = Context({
            'experiment': self.experiment
        })
        doi_xml = render_to_string(template, context_instance=c)
        return doi_xml
