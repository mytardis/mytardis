import json
import logging
from datetime import date

import urllib3
from django.conf import settings
from django.urls import reverse

from tardis.apps.publication_workflow import default_settings
from tardis.apps.publication_workflow import tasks
from tardis.apps.publication_workflow.exceptions import DoiException
from tardis.tardis_portal.models import Experiment, ExperimentAuthor

logger = logging.getLogger(__name__)


class ArdcDOI(object):
    def __init__(self):
        self.prefix = getattr(settings, 'DOI_PREFIX', default_settings.DOI_PREFIX)
        self.username = getattr(settings, 'DOI_USERNAME', default_settings.DOI_USERNAME)
        self.password = getattr(settings, 'DOI_PASSWORD', default_settings.DOI_PASSWORD)
        self.doi_end_point = getattr(settings, 'DOI_ENDPOINT', default_settings.DOI_ENDPOINT)
        self.publisher = getattr(settings, 'DOI_PUBLISHER', default_settings.DOI_PUBLISHER)
        self.doi_mint_root_url = getattr(settings, 'DOI_MINT_ROOT_URL', default_settings.DOI_MINT_ROOT_URL)

        # Set the authentication credentials
        credentials = '{}:{}'.format(self.username, self.password)
        auth_headers = urllib3.util.make_headers(basic_auth=credentials)
        auth_headers["Content-Type"] = "application/vnd.api+json"
        self.http = urllib3.PoolManager(
            num_pools=10,  # number of connection pools to create
            maxsize=10,  # maximum number of connections to keep in each pool
            block=True,  # whether to block when all connections in a pool are in use
            timeout=60,  # connection timeout in seconds
            retries=False,  # whether to retry failed requests
            headers=auth_headers,  # default headers to include with each request
        )

    def mint(self, experiment_id, event='hide'):
        # create draft as default event
        pub = Experiment.objects.get(pk=experiment_id)
        # get the publication year from publication experiment.
        publish_date = tasks.get_release_date(pub)
        publication_year = publish_date.year
        creators = []
        for a in ExperimentAuthor.objects.filter(experiment=pub):
            creators.append({
                "nameType": "Personal",
                "name": a.author
            })

        payload_data = {
            "data": {
                "type": "dois",
                "attributes": {
                    "types": {
                        "resourceTypeGeneral": "Dataset"
                    },
                    "publisher": self.publisher,
                    "publicationYear": publication_year,
                    "titles": [{'title': pub.title}],
                    "creators": creators,
                    "prefix": self.prefix,
                    "event": event,
                    "url": self.doi_mint_root_url + reverse('tardis_portal.view_experiment', args=(experiment_id,))
                }
            }
        }
        payload = json.dumps(payload_data)
        try:
            response = self.http.request(
                'POST',
                url=self.doi_end_point,
                body=payload
            )
            status = response.status

            if status in range(200, 300):
                # get response json
                res_data = json.loads(response.data)
                # get doi json
                doi_data = res_data.get('data')
                # get doi id
                doi = doi_data.get('id')
                return doi
            else:
                error_data = response.data
                res_err = json.loads(error_data)
                logger.error("DOI minting Failed, {}".format(res_err))
                raise Exception(res_err)
        except Exception as ex:
            logger.error("DOI minting could not be completed. See traceback in web response.")
            err_msg = '{}'.format(ex)
            raise DoiException(err_msg)

    def activate(self, doi=None, event='publish'):
        return self.__update_doi(doi, event)

    def deactivate(self, doi=None, event='register'):
        return self.__update_doi(doi, event)

    def __update_doi(self, doi=None, event='register'):
        payload_data = {
            "data": {
                "type": "dois",
                "attributes": {
                    "event": event,
                    "doi": doi
                }
            }
        }

        payload = json.dumps(payload_data)
        try:
            response = self.http.request(
                'PUT',
                url='{}/{}'.format(self.doi_end_point, doi),
                body=payload
            )
            status = response.status
            if status in range(200, 300):
                # get response json
                res_data = json.loads(response.data)
                # get doi json
                doi_data = res_data.get('data')
                # get doi id
                doi = doi_data.get('id')
                return doi
            else:
                error_data = response.data
                res_err = json.loads(error_data)
                logger.error("Updating DOI Failed, {}".format(res_err))
                raise Exception(res_err)
        except Exception as ex:
            logger.error("DOI minting could not be completed. See traceback in web response.")
            err_msg = '{}'.format(ex)
            raise DoiException(err_msg)
