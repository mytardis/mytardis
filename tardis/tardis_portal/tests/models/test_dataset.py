# -*- coding: utf-8 -*-
"""
test_dataset.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from django.contrib.auth.models import Group

from tardis.tardis_portal.models import Dataset, Experiment, Facility, Instrument

from . import ModelTestCase


class DatasetTestCase(ModelTestCase):

    def test_dataset(self):
        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         created_by=self.user)

        exp.save()
        exp2 = Experiment(title='test exp2',
                          institution_name='monash',
                          created_by=self.user)
        exp2.save()

        group = Group(name="Test Manager Group")
        group.save()
        group.user_set.add(self.user)
        facility = Facility(name="Test Facility",
                            manager_group=group)
        facility.save()
        instrument = Instrument(name="Test Instrument",
                                facility=facility)
        instrument.save()

        dataset = Dataset(description='test dataset1')
        dataset.instrument = instrument
        dataset.save()
        dataset.experiments.set([exp, exp2])
        dataset.save()
        dataset_id = dataset.id

        del dataset
        dataset = Dataset.objects.get(pk=dataset_id)

        self.assertEqual(dataset.description, 'test dataset1')
        self.assertEqual(dataset.experiments.count(), 2)
        self.assertIn(exp, list(dataset.experiments.iterator()))
        self.assertIn(exp2, list(dataset.experiments.iterator()))
        self.assertEqual(instrument, dataset.instrument)
        target_id = Dataset.objects.first().id
        self.assertEqual(
            dataset.get_absolute_url(), '/dataset/%d' % target_id,
            dataset.get_absolute_url() + ' != /dataset/%d' % target_id)
