""" ands_doi.py """

import re
import urllib2
from urllib2 import HTTPError
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.importlib import import_module

from tardis.tardis_portal.models import ExperimentParameter, \
    ExperimentParameterSet, ParameterName, Schema

logger = logging.getLogger(__name__)

DOI_NAME = 'doi'  # the ParameterName.name for the DOI


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
        if hasattr(settings, 'DOI_ENABLE') and settings.DOI_ENABLE:
            self.experiment = experiment

            provider = settings.DOI_XML_PROVIDER
            module_name, constructor_name = provider.rsplit('.', 1)

            module = import_module(module_name)
            constructor = getattr(module, constructor_name)

            self.doi_provider = constructor(experiment)
            self.schema = Schema.objects.get(namespace=settings.DOI_NAMESPACE)
            self.doi_name = ParameterName.objects.get(
                schema=self.schema, name=DOI_NAME)

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
        if not doi:
            doi = self._mint_doi(url)
            logger.info("minted DOI %s" % doi)
            self._save_doi(doi)
        return doi

    def get_doi(self):
        """
        :return: DOI or None
        :rtype string
        """
        doi_params = ExperimentParameter.objects.filter(
            name=self.doi_name,
            parameterset__schema=self.schema,
            parameterset__experiment=self.experiment)
        if doi_params.count() == 1:
            return doi_params[0].string_value
        return None

    def _save_doi(self, doi):
        paramset = self._get_or_create_doi_parameterset()
        ep = ExperimentParameter(parameterset=paramset, name=self.doi_name,
                                 string_value=doi)
        ep.save()
        return doi

    def _mint_doi(self, url):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        post_data = 'xml=' + self._datacite_xml()

        base_url = settings.DOI_MINT_URL
        app_id = settings.DOI_APP_ID
        mint_url = "%s?app_id=%s&url=%s" % (base_url, app_id, url)

        doi_response = DOIService._post(mint_url, post_data, headers)
        doi = DOIService._read_doi(doi_response)
        if hasattr(settings, 'DOI_RELATED_INFO_ENABLE') and \
           settings.DOI_RELATED_INFO_ENABLE:
            import tardis.apps.related_info.related_info as ri
            rih = ri.RelatedInfoHandler(self.experiment.id)
            doi_info = {
                ri.type_name: 'website',
                ri.identifier_type_name: 'doi',
                ri.identifier_name: doi,
                ri.title_name: '',
                ri.notes_name: '',
            }
            rih.add_info(doi_info)
        return doi

    def _datacite_xml(self):
        return self.doi_provider.datacite_xml()

    def _get_or_create_doi_parameterset(self):
        eps, _ = ExperimentParameterSet.objects.get_or_create(
            experiment=self.experiment, schema=self.schema)
        return eps

    @staticmethod
    def _read_doi(doi_response):
        matches = re.match(r'\[MT001\] DOI (.+) was successfully minted.',
                           doi_response)
        if not matches:
            raise Exception('unrecognised response: %s' + doi_response)
        return matches.group(1)

    @staticmethod
    def _post(url, post_data, headers):
        try:
            request = urllib2.Request(url, post_data, headers)
            response = urllib2.urlopen(request)
            return response.read()
        except HTTPError as e:
            logger.error(e.read())
            raise e


class DOIXMLProvider(object):
    """
    DOIXMLProvider

    provides datacite XML metadata for a given experiment
    """

    def __init__(self, experiment):
        self.experiment = experiment

    def datacite_xml(self):
        """
        :return: datacite XML for self.experiment
        :rtype: string
        """

        from datetime import date
        from django.template import Context
        import os
        template = os.path.join(settings.DOI_TEMPLATE_DIR, 'default.xml')

        ex = self.experiment
        c = Context()
        c['title'] = ex.title
        c['institution_name'] = ex.institution_name
        c['publication_year'] = date.today().year
        c['creator_names'] = [a.author for a in ex.experimentauthor_set.all()]
        doi_xml = render_to_string(template, context_instance=c)
        return doi_xml
