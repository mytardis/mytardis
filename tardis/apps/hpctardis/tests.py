"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import logging
import re
from os import path
   
from django.test import TestCase
from django.test.client import Client
from django.conf import settings

from tardis.tardis_portal import models
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import ExperimentACL, Experiment, UserProfile



logger = logging.getLogger(__name__)

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


def _grep(string, l):
    expr = re.compile(string)
    match = expr.search(l)
    return match

class SimplePublishTest(TestCase):
    """ Publish Experiments as RIFCS"""
    
    def setUp(self):
        self.client = Client()
        from django.contrib.auth.models import User
        self.username = 'tardis_user1'
        self.pwd = 'secret'
        email = ''
        self.user = User.objects.create_user(self.username, email, self.pwd)
        self.userprofile = UserProfile(user=self.user)
      
      
    def test_publish(self):
        """ Create an experiment and publish it as RIF-CS using RMITANDSService"""
     
        
        
        login = self.client.login(username=self.username,
                                  password=self.pwd)
        self.assertTrue(login)
        
        # Create simple experiment
        exp = models.Experiment(title='test exp1',
                                institution_name='rmit',
                                created_by=self.user,
                                public=True
                                )
        exp.save()
        acl = ExperimentACL(
            pluginId=django_user,
            entityId=str(self.user.id),
            experiment=exp,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
        acl.save()
        
        self.assertEqual(exp.title, 'test exp1')
        self.assertEqual(exp.url, None)
        self.assertEqual(exp.institution_name, 'rmit')
        self.assertEqual(exp.approved, False)
        self.assertEqual(exp.handle, None)
        self.assertEqual(exp.created_by, self.user)
        self.assertEqual(exp.public, True)
        self.assertEqual(exp.get_or_create_directory(),
                         path.join(settings.FILE_STORE_PATH, str(exp.id)))
        
        
        # publish
        data = {'legal':'on',
                'profile':'default.xml'}
        response = self.client.post("/apps/hpctardis/publisher/1/", data)
        
        logger.debug("response=%s" % response)
        
        # check resulting rif-cs
        
        response = self.client.post("/apps/hpctardis/rif_cs/")
        self.assertTrue(_grep("test exp1",str(response)))
        
        
        self.assertTrue(_grep("<key>http://www.rmit.edu.au/HPC/1</key>",str(response)))
        self.assertTrue(_grep("""<addressPart type="text">rmit</addressPart>""",str(response)))
      
        self.assertFalse(_grep("<key>http://www.rmit.edu.au/HPC/2</key>",str(response)))
      
        logger.debug("response=%s" % response)
      