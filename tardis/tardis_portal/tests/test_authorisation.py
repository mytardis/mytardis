import json
import logging

from unittest.mock import patch

from django.test import TestCase
from django.test.client import Client

from django.contrib.auth.models import User, Group, Permission, AnonymousUser

from ..auth.localdb_auth import auth_key as localdb_auth_key
from ..models import ExperimentACL, Experiment

logger = logging.getLogger(__name__)


class ACLTestCase(TestCase):
    urls = 'tardis.urls'

    def setUp(self):

        # create a couple of test users
        self.user1 = User.objects.create_user('testuser1', '', 'secret')
        self.user2 = User.objects.create_user('testuser2', '', 'secret')
        self.user3 = User.objects.create_user('testuser3', '', 'secret')
        self.user4 = User.objects.create_user('testuser4', '', 'secret')

        # with standard permissions
        for user in [self.user1, self.user2, self.user3, self.user4]:
            user.user_permissions.add(Permission.objects.get(codename='add_experiment'))
            user.user_permissions.add(Permission.objects.get(codename='change_experiment'))
            user.user_permissions.add(Permission.objects.get(codename='change_group'))
            user.user_permissions.add(Permission.objects.get(codename='change_userauthentication'))
            user.user_permissions.add(Permission.objects.get(codename='change_experimentacl'))
            user.user_permissions.add(Permission.objects.get(codename='change_datasetacl'))
            user.user_permissions.add(Permission.objects.get(codename='change_datafileacl'))

        self.userProfile1 = self.user1.userprofile
        self.userProfile2 = self.user2.userprofile
        self.userProfile3 = self.user3.userprofile
        self.userProfile4 = self.user4.userprofile

        # each user will have their own client
        self.client1 = Client()
        self.client2 = Client()
        self.client3 = Client()
        self.client4 = Client()

        # user1 will own experiment1
        self.experiment1 = Experiment(
            title='Experiment1',
            institution_name='Australian Synchrotron',
            approved=True,
            public_access=Experiment.PUBLIC_ACCESS_NONE,
            created_by=self.user1,
            )
        self.experiment1.save()

        # user2 will own experiment2
        self.experiment2 = Experiment(
            title='Experiment2',
            institution_name='Australian Synchrotron',
            approved=True,
            public_access=Experiment.PUBLIC_ACCESS_NONE,
            created_by=self.user2,
            )
        self.experiment2.save()

        # experiment3 is public & locked
        self.experiment3 = Experiment(
            title='Experiment3',
            institution_name='Australian Synchrotron',
            approved=True,
            locked=True,
            public_access=Experiment.PUBLIC_ACCESS_FULL,
            created_by=self.user3,
            )
        self.experiment3.save()

        # experiment4 will be accessible based on location information
        self.experiment4 = Experiment(
            title='Experiment4',
            institution_name='Australian Synchrotron',
            approved=True,
            public_access=Experiment.PUBLIC_ACCESS_NONE,
            created_by=self.user1,
            )
        self.experiment4.save()

        # user1 owns experiment1
        acl = ExperimentACL(
            user=self.user1,
            experiment=self.experiment1,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()

        # user2 owns experiment2
        acl = ExperimentACL(
            user=self.user2,
            experiment=self.experiment2,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()

        # experiment4 is NO LONGER accessible via location (as of new ACL update)
        #acl = ObjectACL(
        #    pluginId='ip_address',
        #    entityId='127.0.0.1',
        #    content_object=self.experiment4,
        #    canRead=True,
        #    aclOwnershipType=ObjectACL.SYSTEM_OWNED,
        #)
        #acl.save()

    def tearDown(self):

        self.experiment1.delete()
        self.experiment2.delete()
        self.experiment3.delete()
        #self.experiment4.delete()

        self.user1.delete()
        self.user2.delete()
        self.user3.delete()
        self.user4.delete()

        self.client1.logout()
        self.client2.logout()
        self.client3.logout()
        self.client4.logout()

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def testChangeUserPermissions(self, mock_webpack_get_bundle):
        login1 = self.client1.login(username=self.user1.username,
                                   password='secret')
        self.assertTrue(login1)

        login3 = self.client3.login(username=self.user3.username,
                                   password='secret')
        self.assertTrue(login3)

        # user1 should be see experiment1
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # user3 should not be able to see experiment1
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 403)

        # create a group and add it to experiment1
        response = self.client1.get('/experiment/control_panel'
                                    '/create/group/?group=%s&authMethod=localdb'
                                    % ('group1'))
        self.assertEqual(response.status_code, 200)

        # make the group1 a full read/write/owner of the experiment1
        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/add/group/%s/?canRead=true'
                                    '&canWrite=true&canDelete=false&isOwner=true'
                                    % (self.experiment1.id, 'group1'))
        self.assertEqual(response.status_code, 200)

        # add user3 to experiment1 with no permissions
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="access_list_user')

        # check permissions for user3 - fail as canRead not set to True
        # ACL is auto-deleted as it has no permissions: hence the fail here
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def testReadAccess(self, mock_webpack_get_bundle):
        login = self.client1.login(username=self.user1.username,
                                   password='secret')
        self.assertTrue(login)

        # user1 should be see experiment1
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # user1 should not be allowed to see experiment2
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment2.id))
        self.assertEqual(response.status_code, 403)

        # user1 should be allowed to see experiment3 as it's public
        response = self.client1.get('/experiment/view/%i/'
                                   % (self.experiment3.id))
        self.assertEqual(response.status_code, 200)

        # user1 should be allowed to see experiment4 based on his IP address
        # response = self.client1.get('/experiment/view/%i/'
        #                            % (self.experiment4.id))
        # self.assertEqual(response.status_code, 200)

        # create a group and add it to experiment1
        response = self.client1.get('/experiment/control_panel'
                                    '/create/group/?group=%s&authMethod=localdb'
                                    % ('group1'))
        self.assertEqual(response.status_code, 200)

        # make the group1 a full read/write/owner of the experiment1
        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/add/group/%s/?canRead=true'
                                    '&canWrite=true&canDelete=false&isOwner=true'
                                    % (self.experiment1.id, 'group1'))
        self.assertEqual(response.status_code, 200)

        # add user2 as admin to the newly created group1
        group = Group.objects.get(name='group1')
        response = self.client1.get('/group/%i/add/%s/?isAdmin=true&authMethod=%s'
                                    % (group.id,
                                       self.user2.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 200)

        # try it again
        response = self.client1.get('/group/%i/add/%s/?isAdmin=true&authMethod=%s'
                                    % (group.id,
                                       self.user2.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 400)
        response_dict = json.loads(response.content.decode())
        self.assertEqual(response_dict['field'], 'id_adduser-%s' % group.id)
        self.assertEqual(
            response_dict['message'],
            'User %s is already a member of this group.' % self.user2.username)

        # user1 is not allowed to modify acls for experiment2
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true'
                                    % (self.experiment2.id,
                                       self.user1.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 403)

        # user2 *IS* allowed to modify acls for experiment1, since they are part
        # of an owning group (we add then remove access for user3)
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 200)
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/?authMethod=%s'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

        # test add non-existent user
        non_existent = 'test_boozer'
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true'
                                    % (self.experiment1.id,
                                       non_existent,
                                       localdb_auth_key))

        self.assertContains(
            response, 'User %s does not exist' % non_existent,
            status_code=400)

        # test add to non existent experiment

        # Note: Ideally we'd like to check for error message, but we
        # can't hit it with the decorator in place.  However,
        # currently we check for a 403 (forbidden) error, as the
        # 'experiment_ownership_required' decorator simply checks if
        # the experiment_id appears in the specified user's ACL, and
        # assumes that the absence of the experiment_id means that the
        # experiment exists but the user doesn't have access to
        # it. This could possibly be changed to a 404 error.

        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true' %
                                    (9999, self.user1.username, localdb_auth_key))
        self.assertEqual(response.status_code, 403)

        self.client1.logout()

        # now check user2's permissions
        login = self.client2.login(username=self.user2.username,
                                   password='secret')
        self.assertTrue(login)

        # user2 should be able to see experiment1 now
        response = self.client2.get('/experiment/view/%i/'
                                    % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # user2 should be also able to see experiment2
        response = self.client2.get('/experiment/view/%i/'
                                   % (self.experiment2.id))
        self.assertEqual(response.status_code, 200)

        # user2 should be allowed to see experiment3 as it's public
        response = self.client2.get('/experiment/view/%i/'
                                   % (self.experiment3.id))
        self.assertEqual(response.status_code, 200)

        # user2 should be able to add user3 to group1 (experiment1)
        response = self.client2.get(
            '/group/%i/add/%s/?isAdmin=false&authMethod=%s'
            % (group.id, self.user3.username, localdb_auth_key))
        self.assertEqual(response.status_code, 200)

        self.client2.logout()

        # now check user3's permissions
        login = self.client3.login(username=self.user3.username,
                                   password='secret')
        self.assertTrue(login)

        # user3 should be able to see experiment1 via his group permissions
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # user3 should not be able to see experiment2
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment2.id))
        self.assertEqual(response.status_code, 403)

        # user3 should be able to see experiment3
        response = self.client3.get('/experiment/view/%i/'
                                   % (self.experiment3.id))
        self.assertEqual(response.status_code, 200)

        # user3 should not be able to add another user4 to group1
        response = self.client3.get(
            '/group/%i/add/%s/?isAdmin=false&authMethod=%s'
            % (group.id, 'testuser4', localdb_auth_key))
        self.assertEqual(response.status_code, 403)

        self.client3.logout()

        # Log in as self.client1 again
        login = self.client1.login(username=self.user1.username,
                                   password='secret')
        self.assertTrue(login)

        # remove user3 from group1
        response = self.client1.get('/group/%i/remove/%s/'
                                   % (group.id, self.user3.username))
        self.assertEqual(response.status_code, 200)

        # add user3 to experiment1
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        for acl in self.experiment1.experimentacl_set.all():
            if acl.user is not None:
                logger.debug(str(acl.user.username) +" "+ str(acl.experiment.title) +" "+
                         str(acl.canRead) +" "+str(acl.canWrite) +" "+str(acl.canDelete) +" "+
                         str(acl.isOwner) +" "+str(acl.aclOwnershipType))
            if acl.group is not None:
                logger.debug(str(acl.group.id) +" "+ str(acl.experiment.title) +" "+
                         str(acl.canRead) +" "+str(acl.canWrite) +" "+str(acl.canDelete) +" "+
                         str(acl.isOwner) +" "+str(acl.aclOwnershipType))

            if acl.token is not None:
                logger.debug(str(acl.token.token) +" "+ str(acl.experiment.title) +" "+
                         str(acl.canRead) +" "+str(acl.canWrite) +" "+str(acl.canDelete) +" "+
                         str(acl.isOwner) +" "+str(acl.aclOwnershipType))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="access_list_user')

        # remove user3 from experiment1 again
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/'
                                    % (self.experiment1.id, self.user3.username))
        self.assertEqual(response.content, b'OK')
        self.assertEqual(response.status_code, 200)

        # try again, see if it falls over
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/'
                                    % (self.experiment1.id, self.user3.username))
        self.assertEqual(response.content,
                         b'The user %s does not have access to this experiment.'
                         % self.user3.username.encode())

        # try to remove from a non-existent experiment
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/'
                                    % (9999, self.user3.username))
        self.assertEqual(response.status_code, 403)

        # try to remove the only owner
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/'
                                    % (self.experiment1.id, self.user1.username))
        self.assertEqual(response.content, b'All experiments must have at least '
                                           b'one user as owner. Add an '
                                           b'additional owner first before '
                                           b'removing this one.')

        # create a group2 and add it to experiment1
        response = self.client1.get('/experiment/control_panel'
                                    '/create/group/?group=%s&authMethod=localdb'
                                    % ('group2'))
        self.assertEqual(response.status_code, 200)

        # give group2 read-only access to experiment1
        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/add/group/%s/?canRead=true'
                                    '&canWrite=false&canDelete=false&isOwner=false'
                                    % (self.experiment1.id, 'group2'))
        self.assertEqual(response.status_code, 200)

        # add user3 as admin to group2
        self.group2 = Group.objects.get(name='group2')
        response = self.client1.get(
            '/group/%i/add/%s/?isAdmin=true&authMethod=%s'
            % (self.group2.id,
               self.user3.username,
               localdb_auth_key))
        self.assertEqual(response.status_code, 200)

        # Login as self.client3 again:
        login = self.client3.login(username=self.user3.username,
                                   password='secret')
        self.assertTrue(login)

        # as user3, try to add myself as an owner of the experiment1
        response = self.client3.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true'
                                    '&canWrite=true&canDelete=false&'
                                    'isOwner=true'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        # this should fail since the group2, of which user3 is a member, is
        # not an 'owner' group, just a read-only group
        self.assertEqual(response.status_code, 403)

        # as user3, attempt to remove user1 as the owner of experiment1
        response = self.client3.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/?authMethod=%s'
                                    % (self.experiment1.id,
                                       self.user1.username,
                                       localdb_auth_key))
        # this should fail since the group2, of which user3 is a member, is
        # not an 'owner' group, just a read-only group
        self.assertEqual(response.status_code, 403)

        # as user1, add user3 as an owner of experiment1
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true'
                                    '&canWrite=true&canDelete=false&'
                                    'isOwner=true'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        # since user1 is an owner user of experiment1, we can add additional
        # owner users to the experiment
        self.assertEqual(response.status_code, 200)

        # as user3 (now an owner), attempt to remove user1 as the owner of
        # experiment1, leaving user3 as the sole owner
        response = self.client3.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/?authMethod=%s'
                                    % (self.experiment1.id,
                                       self.user1.username,
                                       localdb_auth_key))
        # this should now succeed since both user3 and user1 are owners of
        # experiment1, and user3 is allowed to remove other owners (unless they
        # are the only owner user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

        # as user3 (now the only owner), attempts to remove myself as the owner
        # of experiment1
        response = self.client3.get('/experiment/control_panel/%i/access_list'
                                    '/remove/user/%s/?authMethod=%s'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        # this should fail with an error since every experiment must have at
        # least one user owner
        self.assertEqual(response.content,
                         b'All experiments must have at least one user as '
                         b'owner. Add an additional owner first before '
                         b'removing this one.')

        self.client1.logout()
        self.client3.logout()

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def testWriteAccess(self, mock_webpack_get_bundle):
        # without logging in the request should be redirected
        response = self.client1.get('/experiment/edit/%i/' % (self.experiment1.id))
        self.assertEqual(response.status_code, 302)

        # now check access for user1
        login = self.client1.login(username=self.user1.username,
                                   password='secret')
        self.assertTrue(login)
        response = self.client1.get('/experiment/edit/%i/' % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)

        # write access has not been granted for experiment2
        response = self.client1.get('/experiment/edit/%i/' % (self.experiment2.id))
        self.assertEqual(response.status_code, 403)

        # neither experiment3 which is public
        response = self.client1.get('/experiment/edit/%i/' % (self.experiment3.id))
        self.assertEqual(response.status_code, 403)

        # create a group 'group1w' with write permissions
        response = self.client1.get('/experiment/control_panel'
                                    '/create/group/?group=%s&authMethod=localdb'
                                    % ('group1w'))
        self.assertEqual(response.status_code, 200)

        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/add/group/%s/?canRead=true'
                                    '&canWrite=true&canDelete=false&isOwner=undefined'
                                    % (self.experiment1.id, 'group1w'))
        self.assertEqual(response.status_code, 200)

        # add user2 to 'group1w' which gives him write permissions
        group = Group.objects.get(name='group1w')
        response = self.client1.get('/group/%i/add/%s/?isAdmin=false&authMethod=%s'
                                   % (group.id, self.user2.username, localdb_auth_key))
        self.assertEqual(response.status_code, 200)

        # add user3 explicitly to experiment1
        response = self.client1.get('/experiment/control_panel/%i/access_list'
                                    '/add/user/%s/?authMethod=%s&canRead=true'
                                    '&canWrite=true'
                                    % (self.experiment1.id,
                                       self.user3.username,
                                       localdb_auth_key))
        self.assertEqual(response.status_code, 200)

        # check newly created permissions for user2 and user3
        response = self.client2.get('/experiment/edit/%i/' % (self.experiment1.id))
        self.assertEqual(response.status_code, 302)

        response = self.client3.get('/experiment/edit/%i/' % (self.experiment1.id))
        self.assertEqual(response.status_code, 302)

        login = self.client2.login(username=self.user2.username, password='secret')
        self.assertTrue(login)

        login = self.client3.login(username=self.user3.username, password='secret')
        self.assertTrue(login)

        # response = self.client2.get('/experiment/edit/%i/' % (self.experiment1.id))
        # self.assertEqual(response.status_code, 200)

        response = self.client3.get('/experiment/edit/%i/' % (self.experiment1.id))
        self.assertEqual(response.status_code, 200)

        # Now remove group from experiment1:
        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/remove/group/%s/'
                                    % (self.experiment1.id, group.id))
        self.assertEqual(response.status_code, 200)

        # Try to remove the same group we just removed:
        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/remove/group/%s/'
                                    % (self.experiment1.id, group.id))
        self.assertIn(b'No ACL available', response.content)

        # Try to remove a group ID which doesn't exist
        response = self.client1.get('/experiment/control_panel/%i'
                                    '/access_list/remove/group/0/'
                                    % self.experiment1.id)
        self.assertIn(b'Group does not exist', response.content)

        self.client1.logout()
        self.client2.logout()
        self.client3.logout()

    @patch('webpack_loader.loader.WebpackLoader.get_bundle')
    def testCantEditLockedExperiment(self, mock_webpack_get_bundle):
        login = self.client3.login(username=self.user3.username, password='secret')
        self.assertTrue(login)

        # user3 has acl to write to experiment3
        acl = ExperimentACL(
            user=self.user3,
            experiment=self.experiment3,
            canRead=True,
            canWrite=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
        )
        acl.save()

        response = self.client3.get('/experiment/edit/%i/' % (self.experiment3.id))
        self.assertEqual(response.status_code, 403)

        response = self.client3.post('/experiment/edit/%i/' % (self.experiment3.id),
                                     {'anything': True, })
        self.assertEqual(response.status_code, 403)

        acl.delete()
        self.client3.logout()
        self.assertNotEqual(mock_webpack_get_bundle.call_count, 0)


    def testOwnedExperiments(self):
        user = AnonymousUser()
        # not logged in
        class MockRequest:
            pass
        request = MockRequest()
        request.user = user
        num_exps = Experiment.safe.owned(request.user).count()
        self.assertEqual(num_exps, 0)
