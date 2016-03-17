"""
Testing the built-in SFTP server
"""
import time
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from tardis.tardis_portal.models import Experiment, ObjectACL
from tardis.tardis_portal.sftp import DynamicTree, MyTSFTPServerInterface
from tardis.tardis_portal.util import dirname_with_id


class SFTPDTestCase(TestCase):
    """
    full integration test
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass


class DynamicTreeTestCase(TestCase):

    def setUp(self):
        self.user = User(username='testuser')
        self.user.save()
        self.experiment = Experiment(title="sftp test experiment",
                                     created_by=self.user)
        self.experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(self.user.id),
            content_type=ContentType.objects.get_for_model(Experiment),
            object_id=self.experiment.id,
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True
        )
        acl.save()

    def test_simple_children(self):
        tree = DynamicTree()
        tree.name = '/'
        tree.add_path('/test/folder')
        self.assertEqual('test', tree.children.keys()[0])
        self.assertEqual('folder', tree.children['test'].children.keys()[0])

    def test_experiment_list(self):
        server_interface = MyTSFTPServerInterface(None)
        server_interface.user = self.user
        tree = DynamicTree(server_interface)
        tree.name = '/'
        exp_leaf = tree.add_path('experiments')
        self.assertEqual(tree.children.keys()[0], 'experiments')
        exp_leaf.update = exp_leaf.update_experiments()
        self.assertEqual(exp_leaf.children.keys()[0], dirname_with_id(
                self.experiment.title, self.experiment.id))


class MyTSFTPServerInterfaceTestCase(TestCase):

    def setUp(self):
        self.user = User(username='testuser')
        self.user.save()
        self.experiment = Experiment(title="sftp test experiment",
                                     created_by=self.user)
        self.experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(self.user.id),
            content_type=ContentType.objects.get_for_model(Experiment),
            object_id=self.experiment.id,
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True
        )
        acl.save()

    def test_experiments(self):
        server_interface = MyTSFTPServerInterface(None)
        server_interface.user = self.user
        self.assertListEqual(list(server_interface.experiments),
                             [self.experiment])

    def test_experiment_caching(self):
        server_interface = MyTSFTPServerInterface(None)
        server_interface.user = self.user
        self.assertListEqual(list(server_interface.experiments),
                             [self.experiment])
        self.assertTrue(self.user.username in
                        MyTSFTPServerInterface._exps_cache)
        new_experiment = Experiment(title="sftp second test experiment",
                                    created_by=self.user)
        new_experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(self.user.id),
            content_type=ContentType.objects.get_for_model(Experiment),
            object_id=new_experiment.id,
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True
        )
        acl.save()
        self.assertListEqual([self.experiment],
                             list(server_interface.experiments))
        MyTSFTPServerInterface._exps_cache[self.user.username][
            'last_update'] = time.time() - 30
        while time.time() - MyTSFTPServerInterface._exps_cache[
            self.user.username]['last_update'] <\
            MyTSFTPServerInterface._cache_time:
            self.assertTrue(False)
        self.assertListEqual([self.experiment, new_experiment],
                             list(server_interface.experiments))
