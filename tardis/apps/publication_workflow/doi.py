# pylint: disable=E0401
import logging
from datetime import date

from django.conf import settings
from requests import Session
from requests.auth import HTTPDigestAuth
from zeep import Client
from zeep.transports import Transport

from tardis.tardis_portal.models import Experiment, ExperimentAuthor
from . import default_settings

logger = logging.getLogger(__name__)


class DOI():

    def __init__(self, doi=None):
        self.doi = doi
        self.api_id = getattr(settings, 'MODC_DOI_API_ID',
                              default_settings.MODC_DOI_API_ID)
        self.url_root = getattr(settings, 'MODC_DOI_MINT_URL_ROOT',
                                default_settings.MODC_DOI_MINT_URL_ROOT).strip("/")

    def _init_client(self, endpoint):
        session = Session()
        session.auth = HTTPDigestAuth(
            settings.MODC_DOI_API_ID,
            settings.MODC_DOI_API_PASSWORD)
        return Client(endpoint, transport=Transport(session=session))

    def mint(self, experiment_id, uri, publisher="Monash University"):
        client = self._init_client(
            getattr(settings, 'MODC_DOI_MINT_DEFINITION',
                    default_settings.MODC_DOI_MINT_DEFINITION))

        pub = Experiment.objects.get(pk=experiment_id)

        resource = {}

        resource['creators'] = [
            {'creator': {'creatorName': a.author}}
            for a in ExperimentAuthor.objects.filter(experiment=pub)]

        resource['titles'] = [{'title': pub.title}]
        resource['publicationYear'] = date.today().year + 1
        resource['publisher'] = publisher

        url = self.url_root + uri

        logger.info("Minting DOI for URL: %s" % url)
        try:
            response = client.service.MintDoi(
                self.api_id, resource, url)
        except:
            logger.error(
                "DOI minting could not be completed. See traceback in web response.")
            raise

        self.doi = response.doi

        return response.doi

    def activate(self, doi=None):
        if doi is None:
            doi = self.doi

            client = self._init_client(
                getattr(settings, 'MODC_DOI_ACTIVATE_DEFINITION',
                        default_settings.MODC_DOI_ACTIVATE_DEFINITION))
        response = client.service.ActivateDoi(self.api_id, doi=doi)
        return response

    def deactivate(self, doi=None):
        if doi is None:
            doi = self.doi

            client = self._init_client(
                getattr(settings, 'MODC_DOI_DEACTIVATE_DEFINITION',
                        default_settings.MODC_DOI_DEACTIVATE_DEFINITION))
        response = client.service.DeactivateDoi(self.api_id, doi=doi)
        return response

    def __str__(self):
        return self.doi
