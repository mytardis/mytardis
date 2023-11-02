import json
import unittest
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from django_elasticsearch_dsl.test import is_es_online

from tardis.tardis_portal.models import (
    DataFile,
    Dataset,
    Experiment,
    DatafileACL,
    DatasetACL,
    ExperimentACL,
)

from tardis.tardis_portal.tests.api import MyTardisResourceTestCase


@unittest.skipUnless(is_es_online(), "Elasticsearch is offline")
@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class SimpleSearchTest(MyTardisResourceTestCase):
    def setUp(self):
        super().setUp()
        print("Elasticsearch is online?", is_es_online())
        self.out = StringIO()
        call_command("search_index", stdout=self.out, action="delete", force=True)
        call_command("search_index", stdout=self.out, action="rebuild", force=True)

        # add dataset and datafile to experiment
        self.dataset1 = Dataset(description="test_dataset")
        self.dataset1.save()
        self.dataset1.experiments.add(self.testexp)
        self.dataset1.save()

        self.setacl = DatasetACL.objects.create(
            dataset=self.dataset1, user=self.user, canRead=True, isOwner=True
        )

        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset1, filename="test.txt")
        self.datafile.save()

        self.fileacl = DatafileACL.objects.create(
            datafile=self.datafile, user=self.user, canRead=True, isOwner=True
        )

    def test_simple_search_authenticated_user(self):
        response = self.api_client.post(
            "/api/v1/search/", authentication=self.get_credentials()
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data["hits"]["experiment"]), 1)
        self.assertEqual(len(data["hits"]["dataset"]), 1)
        self.assertEqual(len(data["hits"]["datafile"]), 1)

    def test_simple_search_unauthenticated_user(self):
        self.testexp.public_access = 100
        self.testexp.save()
        response = self.api_client.post("/api/v1/search/")
        self.assertEqual(response.status_code, 401)
        # data = json.loads(response.content.decode())
        # self.assertEqual(len(data["hits"]["experiments"]), 1)
        # self.assertEqual(len(data["hits"]["datasets"]), 1)
        # self.assertEqual(len(data["hits"]["datafiles"]), 1)
