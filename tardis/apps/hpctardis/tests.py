"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group
from tempfile import mkdtemp, mktemp
from os import walk, path
from django.conf import settings
from tardis.tardis_portal.models import Experiment, ExperimentParameter, \
    DatafileParameter, DatasetParameter, ExperimentACL, Dataset_File, \
    DatafileParameterSet, ParameterName, GroupAdmin, Schema, \
    Dataset, ExperimentParameterSet, DatasetParameterSet, \
    UserProfile, UserAuthentication

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class HPCprotocolTest(TestCase):
    
    user = 'tardis_user1'
    pwd = 'secret'
    email = 'tardis@gmail.com'
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(self.user, self.email, self.pwd)
        # TODO extract the only the username form <User:....>
        self.assertEquals(str(User.objects.get(username=self.user)), 'tardis_user1') 
       
    def test_authentication(self):
        from django.core.urlresolvers import reverse
        import os
        import tempfile
        
        url=reverse('tardis.apps.hpctardis.views.login')
        
#       f = open('Test1.txt','wb+')
        temp = tempfile.TemporaryFile()
        temp.write("Username:venki\nName:Venki Bala\nExperiment:Test Exp\nFacility:localhost\nDescription:Test desc")   
        temp.seek(0)
#       f.close()        
        
#       f = open('Test1.txt','r')
        response = self.client.post(url, {'username':self.user, 
                                               'password':self.pwd, 
                                               'authMethod':'localdb','file':temp}) 
        temp.close()
        self.assertEquals(response.status_code, 200)
        
        str_response = str(response.content)    
        checkuser = response.content.find(str(self.user))
        self.assertEquals(checkuser >= 0, True)
        
        content_list = []
        content_list = str_response.split(str(self.user))     
        self.assertEquals((str(settings.STAGING_PATH) + '/'),content_list[0])
        
     #   self.assertEquals(self.user, checkuser)
        
        content_list = content_list[1].split('/')
        staging = path.join(settings.STAGING_PATH ,str(self.user),content_list[1])
        self.assertEquals(response.content, staging)

        content_list = content_list[1].split('@')
        expid1 = int(content_list[0])
        expid2 = int(content_list[1])
        self.assertEquals(expid1,expid2)
        
     #  Test for Creation of experiment
        
        try:
            e = Experiment.objects.get(pk=expid1)
        except Experiment.DoesNotExist:
            logger.exception('Experiment for eid %i in TestCase does not exist' % eid)
     
        self.assertEquals(str(e.title).rstrip('\n'),'Test Exp')
        self.assertEquals(str(e.institution_name),'RMIT University')
        self.assertEquals(str(e.description),'Test desc')
        self.assertEquals(str(e.created_by),str(self.user))
        
        