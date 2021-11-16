'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase

from tastypie.test import ResourceTestCaseMixin

from ...auth.authservice import AuthService
from ...models.access_control import ExperimentACL
from ...models.experiment import Experiment
from ...models.facility import Facility
from ...models.instrument import Instrument


class MyTardisResourceTestCase(ResourceTestCaseMixin, TestCase):
    '''
    abstract class without tests to combine common settings in one place
    '''
    def setUp(self):
        super().setUp()
        self.PUBLIC_USER = User.objects.create_user(username='PUBLIC_USER')
        self.assertEqual(self.PUBLIC_USER.id, settings.PUBLIC_USER_ID)

        self.username = 'mytardis'
        self.password = 'mytardis'  # nosec
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)
        self.admin_username = 'admin'
        self.admin_password = 'admin'  # nosec
        self.admin_user = User.objects.create_user(
            username=self.admin_username, password=self.admin_password,
            is_superuser=True)
        test_auth_service = AuthService()
        test_auth_service._set_user_from_dict(  # pylint: disable=W0212
            self.user,
            user_dict={'first_name': 'Testing',
                       'last_name': 'MyTardis API',
                       'email': 'api_test@mytardis.org'},
            auth_method="None")
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_experiment'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_dataset'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='add_datafile'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='add_instrument'))
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_instrument'))
        self.user_profile = self.user.userprofile
        self.testgroup = Group(name="Test Group")
        self.testgroup.save()
        self.testgroup.user_set.add(self.user)
        self.testfacility = Facility(name="Test Facility",
                                     manager_group=self.testgroup)
        self.testfacility.save()
        self.testinstrument = Instrument(name="Test Instrument",
                                         facility=self.testfacility)
        self.testinstrument.save()
        self.testexp = Experiment(title="test exp")
        self.testexp.approved = True
        self.testexp.created_by = self.user
        self.testexp.locked = False
        self.testexp.save()
        testacl = ExperimentACL(
            experiment=self.testexp,
            user=self.user,
            canRead=True,
            canDownload=True,
            canWrite=True,
            canSensitive=True,
            canDelete=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED)
        testacl.save()

    def get_credentials(self):
        return self.create_basic(username=self.username,
                                 password=self.password)

    def get_admin_credentials(self):
        return self.create_basic(username=self.admin_username,
                                 password=self.admin_password)

    def get_apikey_credentials(self):
        return self.create_apikey(username=self.username,
                                  api_key=self.user.api_key.key)
