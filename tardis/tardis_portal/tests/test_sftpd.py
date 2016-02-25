"""
Testing the built-in SFTP server
"""
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from tardis.tardis_portal.models import Experiment, ObjectACL
from tardis.tardis_portal.sftp import DynamicTree, MyTSFTPServerInterface
from tardis.tardis_portal.util import dirname_with_id


class SFTPDTestCase(TestCase):

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
