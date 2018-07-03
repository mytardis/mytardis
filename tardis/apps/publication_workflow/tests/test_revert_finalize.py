'''
Tests relating to reverting a publication to a draft
and finalizing a publication
'''
import json
from datetime import timedelta
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.test import TestCase

import dateutil.parser
import pytz

from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.access_control import ObjectACL
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.parameters import ExperimentParameter
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema

from .. import default_settings
from ..models import Publication
from ..tasks import process_embargos
from ..views import (
    retrieve_released_pubs_list,
    finalize_publication)


class RevertFinalizeTestCase(TestCase):
    def setUp(self):
        username = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(username, email, pwd)

        self.draft_pub = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication Draft',
            'Publication draft description')

        self.test_exp1 = Experiment(
            title='test exp1', institution_name='monash',
            created_by=self.user)

        self.test_exp1.save()

        self.acl = ObjectACL(
            pluginId='django_user',
            entityId=str(self.user.id),
            content_object=self.test_exp1,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        self.acl.save()

        self.test_dataset1 = Dataset(description='test dataset1')
        self.test_dataset1.save()
        self.test_dataset1.experiments.set([self.test_exp1])
        self.test_dataset1.save()

        self.form_state = {
            "publicationId": self.draft_pub.id,
            "extraInfo": {},
            "publicationDescription": self.draft_pub.description,
            "publicationTitle": self.draft_pub.title,
            "disciplineSpecificFormTemplates": [],
            "authors": [
                {
                    "email": "testuser1@example.com",
                    "name": "Test User1",
                    "institution": "Test Institute"
                }
            ],
            "action": "submit",
            "acknowledgements": "",
            "addedDatasets": [
                {
                    "experiment": self.test_exp1.title,
                    "experiment_id": self.test_exp1.id,
                    "dataset": {
                        "directory": None,
                        "id": self.test_dataset1.id,
                        "description": self.test_dataset1.description
                    }
                }
            ],
            "embargo": "2018-06-07T05:57:49.510Z",
            "selectedLicenseId": 1
        }

        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        form_state_param_name = ParameterName.objects.get(
            schema=publication_root_schema, name='form_state')
        form_state_parameter = ExperimentParameter.objects.get(
            name=form_state_param_name,
            parameterset__experiment=self.draft_pub)
        form_state_parameter.string_value = json.dumps(self.form_state)
        form_state_parameter.save()

    def test_revert_publication_to_draft(self):
        '''
        Test reverting a publication to a draft
        '''
        self.assertTrue(self.draft_pub.is_publication_draft())
        factory = RequestFactory()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(self.form_state),
            content_type='application/json')
        request.user = self.user
        self.draft_pub.remove_draft_status()
        self.assertFalse(self.draft_pub.is_publication_draft())
        self.assertTrue(self.draft_pub.revert_to_draft())
        self.assertTrue(self.draft_pub.is_publication_draft())

    def test_finalize_publication(self):
        '''
        Test finalizing a publication
        '''
        self.assertTrue(self.draft_pub.is_publication_draft())
        self.draft_pub.remove_draft_status()
        factory = RequestFactory()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(self.form_state),
            content_type='application/json')
        request.user = self.user
        self.assertEqual(
            self.draft_pub.public_access,
            Experiment.PUBLIC_ACCESS_NONE)
        self.draft_pub.set_embargo_release_date(
            datetime.now(pytz.utc) + timedelta(days=1))
        # Normally process_embargos is run asynchronously, but
        # in unit tests it should be run synchronously from within
        # the finalize_publication method, due to the
        # CELERY_ALWAYS_EAGER setting in tardis/test_settings.py:
        finalize_publication(request, self.draft_pub)
        self.assertFalse(self.draft_pub.is_publication_draft())
        self.assertEqual(self.draft_pub.public_access, Experiment.PUBLIC_ACCESS_EMBARGO)

        self.assertTrue(self.draft_pub.revert_to_draft())
        self.draft_pub.remove_draft_status()
        self.draft_pub.set_embargo_release_date(
            datetime.now(pytz.utc) - timedelta(days=1))
        finalize_publication(request, self.draft_pub)
        self.assertEqual(self.draft_pub.public_access, Experiment.PUBLIC_ACCESS_FULL)
