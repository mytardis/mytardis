# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.parameters import (
    DatafileParameter,
    DatafileParameterSet,
    ParameterName,
    Schema,
)
from tardis.tardis_portal.tasks import df_save_metadata


class DatafileSaveMetadataTestCase(TestCase):
    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username="PUBLIC_USER_TEST")
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        self.schema = Schema.objects.create(
            name="DataFile Schema 1",
            namespace="http://schema.namespace/datafile/1",
            type=Schema.DATAFILE,
        )
        self.param1_name = ParameterName.objects.create(
            schema=self.schema, name="param1_name", data_type=ParameterName.STRING
        )
        self.param2_name = ParameterName.objects.create(
            schema=self.schema, name="param2_name", data_type=ParameterName.NUMERIC
        )
        self.dataset = Dataset.objects.create(description="Test dataset")
        self.datafile = DataFile.objects.create(
            dataset=self.dataset, filename="testfile.txt", size=42, md5sum="bogus"
        )

    def tearDown(self):
        self.schema.delete()
        self.dataset.delete()

    def test_df_save_metadata(self):
        """Test the DataFile metadata saving task used by the post-save filters
        microservice
        """
        psets = DatafileParameterSet.objects.filter(datafile=self.datafile)
        self.assertEqual(psets.count(), 0)

        metadata = {"param1_name": "param1 value"}

        # Use a valid existing schema:
        df_save_metadata(
            self.datafile.id, self.schema.name, self.schema.namespace, metadata
        )
        psets = DatafileParameterSet.objects.filter(datafile=self.datafile)
        self.assertEqual(psets.count(), 1)
        df_param = DatafileParameter.objects.filter(parameterset=psets.first()).first()
        self.assertEqual(df_param.string_value, "param1 value")

        # Use a schema which doesn't exist:
        df_save_metadata(
            self.datafile.id, "New schema name", "http://new.schema.namespace", metadata
        )
        new_schema = Schema.objects.filter(
            name="New schema name", namespace="http://new.schema.namespace"
        ).first()
        self.assertIsNotNone(new_schema)
        new_schema.delete()

        metadata = {"param1_name": ["param1 value1", "param1 value2"]}
        for pset in DatafileParameterSet.objects.filter(datafile=self.datafile):
            pset.delete()
        df_save_metadata(
            self.datafile.id, self.schema.name, self.schema.namespace, metadata
        )
        psets = DatafileParameterSet.objects.filter(datafile=self.datafile)
        self.assertEqual(psets.count(), 1)
        df_params = DatafileParameter.objects.filter(
            parameterset=psets.first()
        ).values_list("string_value", flat=True)
        self.assertEqual(sorted(list(df_params)), ["param1 value1", "param1 value2"])

        metadata = {"param2_name": 12345}
        for pset in DatafileParameterSet.objects.filter(datafile=self.datafile):
            pset.delete()
        df_save_metadata(
            self.datafile.id, self.schema.name, self.schema.namespace, metadata
        )
        psets = DatafileParameterSet.objects.filter(datafile=self.datafile)
        self.assertEqual(psets.count(), 1)
        df_param = DatafileParameter.objects.filter(parameterset=psets.first()).first()
        self.assertEqual(df_param.numerical_value, 12345)
