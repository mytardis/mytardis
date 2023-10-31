import os
import unittest
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, modify_settings, override_settings

from tardis.apps.search.documents import (
    DataFileDocument,
    DatasetDocument,
    ExperimentDocument,
)
from tardis.tardis_portal.models import DataFile, Dataset, Experiment


from django_elasticsearch_dsl.test import is_es_online


@unittest.skipUnless(is_es_online(), "Elasticsearch is offline")
@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=True)
class IndexExperimentTestCase(TestCase):
    def setUp(self):
        print("Elasticsearch is online?", is_es_online())

        user = "tardis_user1"
        pwd = "secret"
        email = ""
        self.user = User.objects.create_user(user, email, pwd)
        self.out = StringIO()
        call_command("search_index", stdout=self.out, action="delete", force=True)

    def test_create_index(self):
        self.exp1 = Experiment(
            title="test exp1",
            institution_name="monash",
            description="Test Description",
            created_by=self.user,
        )
        self.exp2 = Experiment(
            title="test exp2",
            institution_name="monash",
            description="Test Description",
            created_by=self.user,
        )
        self.exp1.save()
        self.exp2.save()
        # get search instance
        search = ExperimentDocument.search()
        # query for title(exact matching)
        query = search.query("match", title="test exp1")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].title, "test exp1")
        # query for description
        query = search.query("match", description="Test Description")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].description, "Test Description")
        # query for created_time
        query = search.query("match", created_time=self.exp1.created_time)
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].created_time, self.exp1.created_time)
        # dataset
        # dataset1 belongs to experiment1
        self.dataset1 = Dataset(description="test_dataset")
        self.dataset1.save()
        self.dataset1.experiments.add(self.exp1)
        self.dataset1.save()

        # dataset2 belongs to experiment2
        self.dataset2 = Dataset(description="test_dataset2")
        self.dataset2.save()
        self.dataset2.experiments.add(self.exp2)
        self.dataset2.save()
        # search on dataset
        search = DatasetDocument.search()
        query = search.query("match", description="test_dataset")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits.total.value, 1)
        # search on datafile
        settings.REQUIRE_DATAFILE_SIZES = False
        settings.REQUIRE_DATAFILE_CHECKSUMS = False
        self.datafile = DataFile(dataset=self.dataset1, filename="test.txt")
        self.datafile.save()
        search = DataFileDocument.search()
        query = search.query("match", filename="test.txt")
        result = query.execute(ignore_cache=True)
        self.assertEqual(result.hits[0].filename, self.datafile.filename)
