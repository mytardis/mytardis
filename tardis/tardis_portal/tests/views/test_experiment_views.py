"""
test_experiment_views.py

Tests for view methods relating to experiments

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import json
from urllib.parse import urlparse

from unittest.mock import patch

from django.conf import settings
from django.urls import resolve, reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Permission

from ...models import ExperimentACL, Experiment, Dataset


class ExperimentTestCase(TestCase):

    def setUp(self):
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER_TEST')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)
        # Create test owner without enough details
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)
        for perm in ('add_experiment', 'change_experiment'):
            user.user_permissions.add(Permission.objects.get(codename=perm))
        user.save()
        # Data used in tests
        self.user, self.username, self.password = (user, username, password)
        self.userprofile = self.user.userprofile

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def test_create_and_edit(self, mock_webpack_get_bundle):

        # Login as user
        client = Client()
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        ##########
        # Create #
        ##########

        create_url = reverse('tardis.tardis_portal.views.create_experiment')

        # Check the form is accessible
        response = client.get(create_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # Create client and go to account management URL
        data = {'title': 'The Elements',
                'authors': 'Tom Lehrer, Arthur Sullivan',
                'institution_name': 'The University of California',
                'description':
                "There's antimony, arsenic, aluminum, selenium," +
                "And hydrogen and oxygen and nitrogen and rhenium..."
                }
        response = client.post(create_url, data=data)
        # Expect redirect to created experiment
        self.assertEqual(response.status_code, 303)
        created_url = response['Location']

        # Check that it redirects to a valid location
        response = client.get(created_url)
        self.assertEqual(response.status_code, 200)

        experiment_id = resolve(urlparse(created_url).path)\
            .kwargs['experiment_id']
        experiment = Experiment.objects.get(id=experiment_id)
        for attr in ('title', 'description', 'institution_name'):
            self.assertEqual(getattr(experiment, attr), data[attr])

        # Check authors were created properly
        self.assertEqual(
            [a.author for a in experiment.experimentauthor_set.all()],
            data['authors'].split(', '))

        acl = ExperimentACL.objects.get(experiment=experiment,
                                        user=self.user)
        self.assertTrue(acl.canRead)
        self.assertTrue(acl.canWrite)
        self.assertTrue(acl.isOwner)

        ########
        # Edit #
        ########

        edit_url = reverse('tardis.tardis_portal.views.edit_experiment',
                           kwargs={'experiment_id': str(experiment_id)})

        # Check the form is accessible
        response = client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Create client and go to account management URL
        data = {
            'title': 'I Am the Very Model of a Modern Major-General',
            'authors': (
                'W. S. Gilbert(http://en.wikipedia.org/wiki/'
                'W._S._Gilbert), Arthur Sullivan (arthur@sullivansite.net)'),
            'institution_name': 'Savoy Theatre',
            'description':
                "I am the very model of a modern Major-General," +
                "I've information vegetable, animal, and mineral,"
        }
        response = client.post(edit_url, data=data)
        # Expect redirect to created experiment
        self.assertEqual(response.status_code, 303)
        edit_url = response['Location']

        # Check that it redirects to a valid location
        response = client.get(created_url)
        self.assertEqual(response.status_code, 200)

        experiment_id = resolve(urlparse(created_url).path)\
            .kwargs['experiment_id']
        experiment = Experiment.objects.get(id=experiment_id)
        for attr in ('title', 'description', 'institution_name'):
            self.assertEqual(getattr(experiment, attr), data[attr])

        # Check authors were created properly
        self.assertEqual(
            [a.author for a in experiment.experimentauthor_set.all()],
            ['W. S. Gilbert', 'Arthur Sullivan'])
        self.assertEqual(
            [a.url for a in experiment.experimentauthor_set.all()],
            ['http://en.wikipedia.org/wiki/W._S._Gilbert', None])
        self.assertEqual(
            [a.email for a in experiment.experimentauthor_set.all()],
            [None, 'arthur@sullivansite.net'])

    def test_dataset_json(self):
        user = self.user

        # Create test experiment and make user the owner of it
        def create_experiment(i):
            experiment = Experiment(title='Text Experiment #%d' % i,
                                    institution_name='Test Uni',
                                    created_by=user)
            experiment.save()
            acl = ExperimentACL(user=user,
                                experiment=experiment,
                                canRead=True,
                                isOwner=True,
                                aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
            acl.save()
            return experiment

        experiments = list(map(create_experiment, range(1, 6)))
        experiment = experiments[0]

        # Create some datasets
        def create_dataset(i):
            dataset = Dataset.objects.create(description="Dataset #%d" % i)
            dataset.experiments.add(experiment)
            dataset.save()
            return (dataset.id, dataset)
        datasets = dict(map(create_dataset, range(1, 11)))

        # Login as user
        client = Client()
        login = client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        # Get JSON
        json_url = reverse(
            'tardis.tardis_portal.views.experiment_datasets_json',
            kwargs={'experiment_id': str(experiment.id)})

        # How to check items
        def check_item(item):
            self.assertIn('id', item, "Missing dataset ID")
            dataset = datasets[item['id']]
            # Check attributes
            self.assertEqual(item['description'], dataset.description)
            self.assertEqual(item['immutable'], dataset.immutable)
            # Check experiment list is the same
            self.assertEqual(
                frozenset(item['experiments']),
                frozenset(dataset.experiments .values_list('id', flat=True)))

        # Check the JSON
        response = client.get(json_url)
        self.assertEqual(response.status_code, 200)
        items = json.loads(response.content.decode())
        for item in items:
            check_item(item)
            # Check there's an individual resource
            response = client.get(json_url+str(item['id']))
            self.assertEqual(response.status_code, 200)
            item = json.loads(response.content.decode())
            check_item(item)
            # Attempt to remove the dataset from the original experiment
            # Should fail because it would leave the dataset orphaned
            response = client.delete(json_url+str(item['id']),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 403)
            # Add the dataset to another experiment with PUT
            new_url = reverse('tardis.tardis_portal.views.dataset_json',
                              kwargs={'experiment_id': str(experiments[1].id),
                                      'dataset_id': item['id']})
            response = client.put(new_url,
                                  data=json.dumps(item),
                                  content_type='application/json')
            item = json.loads(response.content.decode())
            check_item(item)
            # This dataset should now have two experiments
            self.assertEqual(
                sorted(item['experiments']),
                sorted([e.id for e in experiments[:2]]))
            # Add the rest of the experiments to the dataset
            item['experiments'] = [e.id for e in experiments]
            # Send the revised dataset back to be altered with PUT
            response = client.put(json_url+str(item['id']),
                                  data=json.dumps(item),
                                  content_type='application/json')
            self.assertEqual(response.status_code, 200)
            item = json.loads(response.content.decode())
            check_item(item)
            self.assertEqual(
                sorted(item['experiments']),
                sorted([e.id for e in experiments]))
            # Remove the dataset from the original experiment
            # Should succeed because there are now many more experiments
            response = client.delete(json_url+str(item['id']),
                                     content_type='application/json')
            self.assertEqual(response.status_code, 200)
            item = json.loads(response.content.decode())
            check_item(item)
            # Expect the item is now in all but the first experiment
            self.assertEqual(
                sorted(item['experiments']),
                sorted([e.id for e in experiments][1:]))
            # Check it no longer exists
            response = client.get(json_url+str(item['id']))
            self.assertEqual(response.status_code, 404)
