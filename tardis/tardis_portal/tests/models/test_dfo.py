# -*- coding: utf-8 -*-
"""
tests_datafileobject.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from django.conf import settings

from tardis.tardis_portal.models import DataFile, DataFileObject, Dataset

from . import ModelTestCase


class DataFileObjectTestCase(ModelTestCase):
    def test_deleting_dfo_without_uri(self):
        dataset = Dataset(description="dataset description")
        dataset.save()
        save1 = settings.REQUIRE_DATAFILE_SIZES
        save2 = settings.REQUIRE_DATAFILE_CHECKSUMS
        try:
            settings.REQUIRE_DATAFILE_SIZES = False
            settings.REQUIRE_DATAFILE_CHECKSUMS = False
            datafile = DataFile(dataset=dataset, filename="test1.txt")
            datafile.save()
        finally:
            settings.REQUIRE_DATAFILE_SIZES = save1
            settings.REQUIRE_DATAFILE_CHECKSUMS = save2
        dfo = DataFileObject(
            datafile=datafile, storage_box=datafile.get_default_storage_box(), uri=None
        )
        dfo.save()
        self.assertIsNone(dfo.uri)
        self.assertIsNotNone(dfo.id)
        dfo.delete()
        self.assertIsNone(dfo.id)
