# -*- coding: utf-8 -*-
"""
test_instrument.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from django.contrib.auth.models import Group

from tardis.tardis_portal.models import (
    Facility,
    Instrument,
    InstrumentParameterSet,
    ParameterName,
    Schema,
)

from . import ModelTestCase


class InstrumentTestCase(ModelTestCase):
    def test_instrument(self):
        group = Group(name="Test Manager Group")
        group.save()
        facility = Facility(name="Test Facility", manager_group=group)
        facility.save()
        self.assertEqual(str(facility), "Test Facility")
        instrument = Instrument(name="Test Instrument", facility=facility)
        instrument.save()
        self.assertEqual(str(instrument), "Test Instrument")

        self.assertEqual(len(instrument.getParameterSets()), 0)

        schema = Schema(
            namespace="test instrument schema namespace", type=Schema.INSTRUMENT
        )
        schema.save()

        parname = ParameterName(schema=schema, name="name", full_name="full_name")
        parname.save()

        pset = InstrumentParameterSet.objects.create(
            instrument=instrument, schema=schema
        )
        pset.save()
        self.assertEqual(len(instrument.getParameterSets()), 1)
