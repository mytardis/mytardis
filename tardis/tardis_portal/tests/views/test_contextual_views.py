"""
test_contextual_views.py

Tests for view methods supplying context data to templates

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
from flexmock import flexmock

from django.test import TestCase
from django.contrib.auth.models import User

from ...models import \
    ExperimentACL, Experiment, Dataset, DataFile, Schema, \
    DatafileParameterSet


class ContextualViewTest(TestCase):

    def setUp(self):
        """
        setting up essential objects, copied from tests above
        """
        user = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(user, email, pwd)
        self.exp = Experiment(title='test exp1',
                              institution_name='monash', created_by=self.user)
        self.exp.save()
        self.acl = ExperimentACL(
            user=self.user,
            experiment=self.exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        self.acl.save()
        self.dataset = Dataset(description='dataset description...')
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        self.datafile = DataFile(dataset=self.dataset,
                                 size=42, filename="foo",
                                 md5sum="junk")
        self.datafile.save()

        self.testschema = Schema(namespace="http://test.com/test/schema",
                                 name="Test View",
                                 type=Schema.DATAFILE,
                                 hidden=True)
        self.testschema.save()
        self.dfps = DatafileParameterSet(datafile=self.datafile,
                                         schema=self.testschema)
        self.dfps.save()

    def tearDown(self):
        self.user.delete()
        self.exp.delete()
        self.dataset.delete()
        self.datafile.delete()
        self.testschema.delete()
        self.dfps.delete()
        self.acl.delete()

    def test_details_display(self):
        """
        test display of view for an existing schema and no display for an
        undefined one.
        """
        from ...views.ajax_pages import display_datafile_details
        request = flexmock(user=self.user, groups=[("testgroup", flexmock())])
        with self.settings(DATAFILE_VIEWS=[
                ("http://test.com/test/schema", "/test/url"),
                ("http://does.not.exist", "/false/url")]):
            response = display_datafile_details(
                request, datafile_id=self.datafile.id)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"/ajax/parameters/" in response.content)
            self.assertTrue(b"/test/url" in response.content)
            self.assertFalse(b"/false/url" in response.content)
