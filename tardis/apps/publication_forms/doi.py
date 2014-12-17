from datetime import date

from django.conf import settings
from suds.client import Client

from tardis.tardis_portal.models import Experiment, ExperimentAuthor


class DOI_minter():

    def __init__(self):
        self.api = Client(settings.MODC_DOI_DEFINITION,
                          location=settings.MODC_DOI_ENDPOINT)
        self.api_id = settings.MODC_DOI_API_ID
        self.url_root = settings.MODC_DOI_MINT_URL_ROOT

    def mint(self, experiment_id, uri, publisher="Monash University"):
        pub = Experiment.objects.get(pk=experiment_id)

        resource = {}

        resource['creators'] = [{'creator':{'creatorName': a.author}}
                                for a in ExperimentAuthor.objects.filter(experiment=pub)]

        resource['titles'] = [{'title':pub.title}]
        resource['publicationYear'] = date.today().year + 1
        resource['publisher'] = publisher

        response = self.api.service.MintDoi(self.api_id, resource, self.url_root+uri)

        return response.doi
