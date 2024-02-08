# -*- coding: utf-8 -*-
"""
test_authors.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from tardis.tardis_portal.models import Experiment, ExperimentAuthor

from . import ModelTestCase


class AuthorTestCase(ModelTestCase):
    def test_authors(self):
        exp = Experiment(
            title="test exp2",
            institution_name="monash",
            created_by=self.user,
        )
        exp.save()

        ExperimentAuthor(experiment=exp, author="nigel", order=0).save()

        exp = Experiment(
            title="test exp1",
            institution_name="monash",
            created_by=self.user,
        )
        exp.save()

        ae1 = ExperimentAuthor(experiment=exp, author="steve", order=100)
        ae1.save()

        ae2 = ExperimentAuthor(experiment=exp, author="russell", order=1)
        ae2.save()

        ae3 = ExperimentAuthor(experiment=exp, author="uli", order=50)
        ae3.save()

        authors = exp.experimentauthor_set.all()

        # confirm that there are 2 authors
        self.assertEqual(len(authors), 3)
        self.assertTrue(ae1 in authors)
        self.assertTrue(ae2 in authors)
        self.assertTrue(ae3 == authors[1])
