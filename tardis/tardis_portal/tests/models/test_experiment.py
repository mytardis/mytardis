# -*- coding: utf-8 -*-
"""
test_experiment.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import os

from django.conf import settings

from tardis.tardis_portal.models import Experiment

from . import ModelTestCase


class ExperimentTestCase(ModelTestCase):

    def test_experiment(self):
        exp = Experiment(title='test exp1',
                         institution_name='monash',
                         created_by=self.user)
        exp.save()
        self.assertEqual(exp.title, 'test exp1')
        self.assertEqual(exp.url, None)
        self.assertEqual(exp.institution_name, 'monash')
        self.assertEqual(exp.approved, False)
        self.assertEqual(exp.handle, None)
        self.assertEqual(exp.created_by, self.user)
        self.assertEqual(exp.public_access,
                         Experiment.PUBLIC_ACCESS_NONE)
        target_id = Experiment.objects.first().id
        self.assertEqual(
            exp.get_absolute_url(), '/experiment/view/%d/' % target_id,
            exp.get_absolute_url() + ' != /experiment/view/%d/' % target_id)
        self.assertEqual(exp.get_or_create_directory(),
                         os.path.join(settings.FILE_STORE_PATH, str(exp.id)))
