# Copyright (c) 2011-2012, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
RMITANDSService.py

.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>

"""

import os
import random

from tardis.tardis_portal.publish.publishservice import PublishService

from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from tardis.tardis_portal.models import Experiment
import logging


from tardis.apps.hpctardis.models import PublishAuthorisation

from django.utils.hashcompat import sha_constructor

logger = logging.getLogger(__name__)


def _send_email(publish_auth,activation_key, exp, activity,auth_party,
                party_email):
    logger.debug("publish auth=%s" % publish_auth)
    from django.template import Context, Template
    
    TARDIS_ROOT = os.path.abspath(\
                        os.path.join(os.path.dirname(__file__)))
    
    email_path = os.path.join(TARDIS_ROOT,
              "authemail.txt")
    
    
    email_text_fp = open(email_path,"r")
    
    
    email_contents = email_text_fp.read()
    
    t = Template(email_contents)
    d = {"code": activation_key,
         "domain": settings.EMAIL_LINK_HOST,
         "path":"publishauth",
         "exp":exp.id,
         "expname":exp.title,
         "activity": activity,
         "expauthor": exp.created_by,
         "authoriser": auth_party.partyname.given }
    email_to_send =  t.render(Context(d))
    
    from django.core.mail import send_mail
    
    logger.debug("email to send = %s" % email_to_send)
    
    send_mail('Authorisation required for experiment', 
                  email_to_send, 'admin@hpctardis.rmit.edu.au',
                [party_email], fail_silently=False)
    

def send_request_email(auth_party,activity,exp_id):
        """ Make record that describes authkey, address of correspondance,
            and state of authorisation.  Send email to address, and wait for 
            verification.
        """
    
        exp = Experiment.objects.get(pk=exp_id)    
  
    
        try:
            party_email = auth_party.get_email_addresses()[0]
        except IndexError:
            party_email = ""
        
        try:
            publish_auth= PublishAuthorisation.objects.get(experiment=exp,
                                                        party_record=auth_party)
        except PublishAuthorisation.DoesNotExist:
               
            
            salt = sha_constructor(str(random.random())).hexdigest()[:5]
            logger.debug("salt=%s" % salt)
            username = unicode(auth_party.partyname)
            if isinstance(username, unicode):
                username = username.encode('utf-8')
            logger.debug("usernane=%s" % username)
            activation_key = sha_constructor(salt+username).hexdigest()
            logger.debug("activation_key=%s" % activation_key)
          
                
            logger.debug("party_email=%s" % party_email)
            
        
            publish_auth = PublishAuthorisation(auth_key=activation_key,
                                experiment=exp,
                                authoriser=auth_party.get_fullname(),
                                email=party_email,
                                status=PublishAuthorisation.PENDING_APPROVAL,
                                party_record=auth_party,
                                activity_record=activity)
            
            publish_auth.save()
        
            _send_email(publish_auth=publish_auth,
                        activation_key=activation_key,
                        exp=exp,
                        activity=activity,
                        auth_party=auth_party,
                        party_email=party_email)
            return True
            
           
        except PublishAuthorisation.MultipleObjectsReturned:
            #FIXME: this is an inconsistent state
            # probably want to delete all extra records?
            return False
        else:
            
            logger.debug("already found record")
            
            
            _send_email(publish_auth=publish_auth,
                        activation_key=publish_auth.auth_key,
                        exp=exp,
                        activity=publish_auth.activity_record,
                        auth_party=auth_party,
                        party_email=party_email)
            
            
            logger.debug("publish auth=%s" % publish_auth)
            
            return True
            
            
            
class RMITANDSService(PublishService):
    
    def __init__(self, experiment_id, settings=settings):
        self._publish_providers = []
        self._initialised = False
        self.settings = settings
        self.experiment_id = experiment_id

    def _manual_init(self):
        """Manual init had to be called by all the functions of the PublishService
        class to initialise the instance variables. This block of code used to
        be in the __init__ function but has been moved to its own init function
        to get around the problems with cyclic imports to static variables
        being exported from auth related modules.

        """
        for pp in self.settings.PUBLISH_PROVIDERS:
            self._publish_providers.append(self._safe_import(pp))
        self._initialised = True

    def _safe_import(self, path):
        try:
            dot = path.rindex('.')
        except ValueError:
            raise ImproperlyConfigured(\
                '%s isn\'t a middleware module' % path)
        publish_module, publish_classname = path[:dot], path[dot + 1:]
        try:
            mod = import_module(publish_module)
        except ImportError, e:
            raise ImproperlyConfigured(\
                'Error importing publish module %s: "%s"' %
                                       (publish_module, e))
        try:
            publish_class = getattr(mod, publish_classname)
        except AttributeError:
            raise ImproperlyConfigured(\
                'Publish module "%s" does not define a "%s" class' %
                                       (publish_module, publish_classname))

        publish_instance = publish_class(self.experiment_id)
        return publish_instance

    def get_publishers(self):
        """Return a list publish providers

        """
        if not self._initialised:
            self._manual_init()

        publicaton_list = [pp for pp in self._publish_providers]
        return publicaton_list

    def get_template_paths(self):
        """Returns a list of relative file paths to html templates

        """
        if not self._initialised:
            self._manual_init()
        path_list = []
        for pp in self._publish_providers:
            logger.debug("mygroup provider: %s %s" % (pp.name,pp.get_path()))
            path_list.append(pp.get_path())
        return path_list

    def get_contexts(self, request):
        """Gets context dictionaries for each PublishProvider

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        if not self._initialised:
            self._manual_init()
        contexts = {}
        for pp in self._publish_providers:
            # logger.debug("group provider: " + gp.name)
            context = pp.get_context(request)
            if context:
                contexts = dict(contexts, **context)
        return contexts

    def execute_publishers(self, request):
        """Executes each publish provider in a chain.
        If any publish provider fails then the experiment is not made public

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`
        """
        if not self._initialised:
            self._manual_init()

        pp_status_list = []
        for pp in self._publish_providers:

            pp_status = False
            pp_result = "Successful"

            try:
                pp_response = pp.execute_publish(request)
            except Exception as inst:
                # perhaps erroneous logic to be fixed later..
                exp = Experiment.objects.get(id=self.experiment_id)
                exp.public = False
                exp.save()

                logger.error('Publish Provider Exception: ' +
                pp.name + ' on exp: ' + str(self.experiment_id) +
                ' failed with message "' +
                str(inst) + '""')

                pp_response = {'status': False, 'message': str(inst)}

            if pp_response['status']:
                logger.info('Publish Provider: ' +
                pp.name + ' executed on Exp: ' +
                str(self.experiment_id) + ' with success: ' +
                str(pp_response['status']) + ' and message: ' +
                pp_response['message'])
            else:
                logger.error('Publish Provider: ' +
                pp.name + ' executed on Exp: ' +
                str(self.experiment_id) + ' FAILED with message: ' +
                pp_response['message'])

            pp_status_list.append({'name': pp.name,
            'status': pp_response['status'],
            'message': pp_response['message']})
        return pp_status_list

    def is_under_review(self):
        
        # FIXME: probably should delegate to provider for this functionality
        publish_auths= PublishAuthorisation.objects.filter(
                                            experiment__id=self.experiment_id)    
        
        if publish_auths:        
            logger.debug("publish_auths=%s" % publish_auths)
            for publish_auth in publish_auths:
                if publish_auth.status == PublishAuthorisation.PENDING_APPROVAL:
                    return True
            return False
        else:
            return False
            