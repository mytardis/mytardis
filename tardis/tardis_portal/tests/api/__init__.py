'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
from django.contrib.auth.models import User, Group, Permission
from django.test import TransactionTestCase

from tastypie.test import ResourceTestCaseMixin

from ...auth.authservice import AuthService
from ...auth.localdb_auth import django_user
from ...models.access_control import ObjectACL
from ...models.project import Project
from ...models.experiment import Experiment
from ...models.facility import Facility
from ...models.instrument import Instrument
from ...models.institution import Institution

class MyTardisResourceTestCase(ResourceTestCaseMixin, TransactionTestCase):
    '''
    abstract class without tests to combine common settings in one place
    '''
    def setUp(self):
        super().setUp()
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
        self.testinstitution = Institution(name="Test Institution",
                                     manager_group=self.testgroup)
        self.testinstitution.save()
        self.testfacility = Facility(name="Test Facility",
                                     manager_group=self.testgroup,
                                     institution=self.testinstitution)
        self.testfacility.save()
        self.testinstrument = Instrument(name="Test Instrument",
                                         facility=self.testfacility)
        self.testinstrument.save()
        self.testproject = Project(name="test project", raid='test raid')
        self.testproject.created_by = self.user
        self.testproject.lead_researcher = self.user

        self.testproject.save()
        testacl = ObjectACL(
            content_type=self.testproject.get_ct(),
            object_id=self.testproject.id,
            pluginId=django_user,
            entityId=str(self.user.id),
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED)
        testacl.save()
        self.testexp = Experiment(title="test exp", project=self.testproject)
        self.testexp.approved = True
        self.testexp.created_by = self.user
        self.testexp.locked = False
        self.testexp.save()
        testacl = ObjectACL(
            content_type=self.testexp.get_ct(),
            object_id=self.testexp.id,
            pluginId=django_user,
            entityId=str(self.user.id),
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED)
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
