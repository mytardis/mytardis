'''
Tests relating to publication form
'''
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.test import TestCase

from tardis.tardis_portal.models import (
    Dataset,
    Experiment,
    ObjectACL,
    ExperimentParameter,
    ParameterName,
    Schema)

from .. import default_settings
from ..models import Publication
from ..views import fetch_experiments_and_datasets
from ..views import form_view


class PublicationFormTestCase(TestCase):
    def setUp(self):
        username = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(username, email, pwd)

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

    def test_create_draft_publication(self):
        '''
        Test creating draft publication
        '''
        self.draft_pub = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication',
            'Publication description')
        self.assertTrue(self.draft_pub.is_publication_draft())

    def test_resume_draft_publication(self):
        '''
        Test resuming draft publication
        '''
        self.draft_pub = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication',
            'Publication description')

        form_state = {
            "publicationId": self.draft_pub.id,
            "extraInfo": {},
            "publicationDescription": self.draft_pub.description,
            "publicationTitle": self.draft_pub.title,
            "disciplineSpecificFormTemplates": [],
            "authors": [
                {
                    "email": "",
                    "name": "",
                    "institution": ""
                }
            ],
            "action": "resume",
            "acknowledgements": "",
            "addedDatasets": []
        }

        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        form_state_param_name = ParameterName.objects.get(
            schema=publication_root_schema, name='form_state')
        form_state_parameter = ExperimentParameter.objects.get(
            name=form_state_param_name,
            parameterset__experiment=self.draft_pub)
        form_state_parameter.string_value = json.dumps(form_state)
        form_state_parameter.save()

        factory = RequestFactory()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(form_state),
            content_type='application/json')
        request.user = self.user
        response = form_view(request)
        self.assertEqual(json.loads(response.content), form_state)
        self.assertEqual(response.status_code, 200)

    def test_update_dataset_selection(self):
        '''
        Test updating dataset selection in publication form
        '''
        self.draft_pub = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication',
            'Publication description')

        form_state = {
            "publicationId": self.draft_pub.id,
            "extraInfo": {},
            "publicationDescription": self.draft_pub.description,
            "publicationTitle": self.draft_pub.title,
            "disciplineSpecificFormTemplates": [],
            "authors": [
                {
                    "email": "",
                    "name": "",
                    "institution": ""
                }
            ],
            "action": "update-dataset-selection",
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
            ]
        }

        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        form_state_param_name = ParameterName.objects.get(
            schema=publication_root_schema, name='form_state')
        form_state_parameter = ExperimentParameter.objects.get(
            name=form_state_param_name,
            parameterset__experiment=self.draft_pub)
        form_state_parameter.string_value = json.dumps(form_state)
        form_state_parameter.save()

        self.assertEqual(Dataset.objects.filter(experiments=self.draft_pub).count(), 0)
        factory = RequestFactory()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(form_state),
            content_type='application/json')
        request.user = self.user
        response = form_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Dataset.objects.filter(experiments=self.draft_pub).count(), 1)

    def test_update_extra_info(self):
        '''
        Test updating extra info in publication form
        '''
        self.draft_pub = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication',
            'Publication description')

        form_state = {
            "publicationId": self.draft_pub.id,
            "extraInfo": {
                "0.0": {
                  "dataset": "test dataset1",
                  "description": "some test description for test dataset1",
                  "schema": "http://www.mytardis.org/schemas/publication/generic/"
                }
            },
            "publicationDescription": self.draft_pub.description,
            "publicationTitle": self.draft_pub.title,
            "disciplineSpecificFormTemplates": [],
            "authors": [
                {
                    "email": "",
                    "name": "",
                    "institution": ""
                }
            ],
            "action": "update-extra-info",
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
            ]
        }

        publication_root_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                              default_settings.PUBLICATION_SCHEMA_ROOT))
        form_state_param_name = ParameterName.objects.get(
            schema=publication_root_schema, name='form_state')
        form_state_parameter = ExperimentParameter.objects.get(
            name=form_state_param_name,
            parameterset__experiment=self.draft_pub)
        form_state_parameter.string_value = json.dumps(form_state)
        form_state_parameter.save()

        factory = RequestFactory()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(form_state),
            content_type='application/json')
        request.user = self.user
        response = form_view(request)
        self.assertEqual(response.status_code, 200)
        # Add more assertions here...

    def test_submit_form(self):
        '''
        Test submitting publication form
        '''
        self.draft_pub = Publication.safe.create_draft_publication(
            self.user,
            'Test Publication',
            'Publication description')

        form_state = {
            "publicationId": self.draft_pub.id,
            "extraInfo": {
                "0.0": {
                  "dataset": "test dataset1",
                  "description": "some test description for test dataset1",
                  "schema": "http://www.mytardis.org/schemas/publication/generic/"
                }
            },
            "publicationDescription": self.draft_pub.description,
            "publicationTitle": self.draft_pub.title,
            "disciplineSpecificFormTemplates": [],
            "authors": [
                {
                    "email": "",
                    "name": "",
                    "institution": ""
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
        form_state_parameter.string_value = json.dumps(form_state)
        form_state_parameter.save()

        factory = RequestFactory()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(form_state),
            content_type='application/json')
        request.user = self.user
        response = form_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'You must confirm that you are authorised to submit this publication',
            response.content.decode())
        form_state['acknowledge'] = True
        form_state_parameter.string_value = json.dumps(form_state)
        form_state_parameter.save()
        request = factory.post(
            '/apps/publication-workflow/form/',
            data=json.dumps(form_state),
            content_type='application/json')
        request.user = self.user
        response = form_view(request)
        self.assertEqual(response.status_code, 200)
        # Add more assertions here...

    def test_fetch_experiments_and_datasets(self):
        '''
        Test fetching experiments and datasets for publication form
        '''
        factory = RequestFactory()
        request = factory.get('/apps/publication-workflow/data/fetch_experiments_and_datasets/')
        request.user = self.user
        response = fetch_experiments_and_datasets(request)
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                "id": self.test_exp1.id,
                "title": self.test_exp1.title,
                "institution_name": self.test_exp1.institution_name,
                "description": "",
                "datasets": [
                    {
                        "id": self.test_dataset1.id,
                        "description": self.test_dataset1.description,
                        "directory": None
                    }
                ]
            }
        ]
        self.assertEqual(
            json.loads(response.content),
            expected)
