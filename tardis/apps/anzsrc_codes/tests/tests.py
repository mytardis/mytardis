import re

from compare import expect, ensure, matcher

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse


from tardis.tardis_portal.models import \
    Experiment, ObjectACL, User


def _create_user_and_login(username='testuser', password='testpass'):
    user = User.objects.create_user(username, '', password)
    user.save()

    client = Client()
    client.login(username=username, password=password)
    return (user, client)


class TabTestCase(TestCase):

    def setUp(self):
        user, client = _create_user_and_login()

        experiment = Experiment(title='Norwegian Blue',
                                description='Parrot + 40kV',
                                created_by=user)
        experiment.save()
        acl = ObjectACL(content_object=experiment,
                        pluginId='django_user',
                        entityId=str(user.id),
                        isOwner=False,
                        canRead=True,
                        canWrite=False,
                        canDelete=False,
                        aclOwnershipType=ObjectACL.OWNER_OWNED)
        acl.save()
        self.client = client
        self.experiment = experiment

    def testAccessWithoutReadPerms(self):
        client = Client()
        response = client.get(\
                    reverse('tardis.apps.anzsrc_codes.views.index',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(403)

    def testAccessWithReadPerms(self):
        response = self.client.get(\
                    reverse('tardis.apps.anzsrc_codes.views.index',
                            args=[self.experiment.id]))
        expect(response.status_code).to_equal(200)
