# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of RMIT University nor the
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


'''
RIF CS Profile Module

.. moduleauthor:: Steve Androulakis <steve.androulakis@gmail.com>
.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas>
'''


import os
import logging
import random


from django.forms.formsets import formset_factory

from tardis.tardis_portal.publish.interfaces import PublishProvider
from tardis.tardis_portal.models import Experiment, ExperimentParameter, \
    ParameterName, Schema, ExperimentParameterSet

from tardis.apps.hpctardis.forms import ActivitiesSelectForm
from tardis.apps.hpctardis.models import ActivityPartyRelation
from tardis.apps.hpctardis.models import PartyLocation
from tardis.apps.hpctardis.forms import CollectionPartyRelation
from tardis.apps.hpctardis.models import PublishAuthorisation

from tardis.apps.hpctardis.publish.RMITANDSService import send_request_email


logger = logging.getLogger(__name__)



from itertools import groupby

def paragraphs(lines) :
    """ See http://stackoverflow.com/questions/116494/python-regular-expression-to-split-paragraphs/123806#123806 """
    for group_separator, line_iteration in groupby(lines.splitlines(True),
                                                    key = str.isspace) :
        if not group_separator :
            yield ''.join(line_iteration)


class rif_cs_PublishProvider(PublishProvider):

    def __init__(self, experiment_id):
        self.experiment_id = experiment_id

    name = u'ANDS'

    
        
        
    def execute_publish(self, request):
        """
        Attach the user-selected RIF-CS profile name to the experiment
        as a parameter

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`

        """
        auth_pending = False
        experiment = Experiment.objects.get(id=self.experiment_id)
        activities_select_form = ActivitiesSelectForm(request.POST)
        if activities_select_form.is_valid():
            data = activities_select_form.cleaned_data
            activities = data['activities']
            for activity in activities:     
                logger.debug("processing activity %s" % activity)
                activity_party_relations = ActivityPartyRelation.objects.filter(
                                                    activity=activity,
                                                    relation=u"isManagedBy")
                for activity_party_relation in activity_party_relations:
                    party = activity_party_relation.party
                    logger.debug("authparty for %s is %s" %
                                  (activity.activityname, 
                                   party.get_fullname()))      
                    if send_request_email(party,activity, self.experiment_id):  
                        auth_pending = True 
                        logger.debug("auth_pending=%s" % auth_pending)
                                          
        else:
            return {'status': True,
                'message': 'Invalid activity selection. Please select party record to request authorisation'}
        
        Party_Formset = formset_factory(CollectionPartyRelation,extra=2)        
        party_formset = Party_Formset(request.POST)
        logger.debug("partyloaded")
        logger.debug(party_formset.is_valid())       
        logger.debug(party_formset.errors)
        logger.debug(party_formset.cleaned_data)
        self._del_party_paramsets()
        for form in party_formset:
            data = form.cleaned_data
            if 'party' in data:
                party = data['party']
            else:
                party = None       
            if 'relation' in data:
                relation_name = data['relation']
            else:
                relation_name = None         
            logger.debug("%s %s" % (party, relation_name))
            if party:
                self._save_party_refs(party, relation_name)
                                 
        if request.POST['profile']:
            experiment = Experiment.objects.get(id=self.experiment_id)
            profile = request.POST['profile']
            self.save_rif_cs_profile(experiment, profile)
            logger.debug("auth_pending=%s" % auth_pending)
            if auth_pending:
                return {'status': True,
                        'message': 'Experiment ready of publishing, awaiting authorisation by activity managers'}
            else:
                return {'status': True,
            'message': 'Success'}
        else:
            return {'status': True,
            'message': 'No profiles exist to choose from'}

    def get_context(self, request):
        """
        Display a list of profiles on screen for selection

        :param request: a HTTP Request instance
        :type request: :class:`django.http.HttpRequest`

        """

        rif_cs_profiles = self.get_rif_cs_profile_list()

        selected_profile = "default.xml"

        if self.get_profile():
            selected_profile = self.get_profile()
            
        activity_form = ActivitiesSelectForm() 
        
                    
        Party_Formset = formset_factory(CollectionPartyRelation,extra=2)
        party_formset = Party_Formset()

        return {"rif_cs_profiles": rif_cs_profiles,
                "selected_profile": selected_profile,
                "activity_form": activity_form,
                "party_formset": party_formset}

    def get_path(self):
        """
        Return the relative template file path to display on screen

        :rtype: string
        """
        return "rif_cs_profile/form.html"

    def get_rif_cs_profile_list(self):
        """
        Return a list of the possible RIF-CS profiles that can
        be applied. Scans the profile directory.

        :rtype: list of strings
        """

        # TODO this is not a scalable or pluggable way of listing
        #  or defining RIF-CS profiles. The current method REQUIRES
        #  branching of the templates directory. instead of using the
        #  built in template resolution tools.
        TARDIS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        profile_dir = os.path.join(TARDIS_ROOT,
                      "profiles/")

        logger.debug("profile_dir = %s" % profile_dir)
        profile_list = list()

        try:
            for f in os.listdir(profile_dir):
                if not os.path.isfile(profile_dir + f) or \
                       f.startswith('.') or not f.endswith('.xml'):
                    continue
                profile_list.append(f)
        except OSError:
            logger.error("Can't find profile directory " +
            "or no profiles available")

        return profile_list

    def save_rif_cs_profile(self, experiment, profile):
        """
        Save selected profile choice as experiment parameter
        """
        namespace = "http://monash.edu.au/rif-cs/profile/"
        schema = None
        try:
            schema = Schema.objects.get(
                namespace__exact=namespace)
        except Schema.DoesNotExist:
            logger.debug('Schema ' + namespace +
            ' does not exist. Creating.')
            schema = Schema(namespace=namespace)
            schema.save()

        try:
            parametername = ParameterName.objects.get(
            schema__namespace__exact=schema.namespace,
            name="profile")
        except ParameterName.DoesNotExist:
            logger.debug("profile does not exist. Creating.")
            parametername = ParameterName(name="profile",schema=schema)
            parametername.save()
        

        parameterset = None
        try:
            parameterset = \
                         ExperimentParameterSet.objects.get(\
                                schema=schema,
                                experiment=experiment)

        except ExperimentParameterSet.DoesNotExist, e:
            parameterset = ExperimentParameterSet(\
                                schema=schema,
                                experiment=experiment)

            parameterset.save()

        # if a profile param already exists
        if self.get_profile():
            ep = ExperimentParameter.objects.filter(name=parametername,
            parameterset=parameterset,
            parameterset__experiment__id=self.experiment_id)

            for p in ep:
                p.delete()

        ep = ExperimentParameter(
            parameterset=parameterset,
            name=parametername,
            string_value=profile,
            numerical_value=None)
        ep.save()


    def _del_party_paramsets(self):
        """ Delete all existing party parameter sets 
        """
        namespace = "http://rmit.edu.au/rif-cs/party/1.0/"
        try:
            schema = Schema.objects.get(
                namespace__exact=namespace)
        except Schema.DoesNotExist:
            return 
        exp = Experiment.objects.get(pk=self.experiment_id)    
        parameterset = None
        try:
            parameterset = \
                         ExperimentParameterSet.objects.filter(\
                                schema=schema,
                                experiment=exp)
        except ExperimentParameterSet.DoesNotExist, e:
            return
        parameterset.delete()    
        
    def _make_param(self,schema,name,paramtype):
        try:
            param = ParameterName.objects.get(schema=schema,
                name=name,data_type=paramtype
                )
        except ParameterName.DoesNotExist:
            logger.debug("%s does not exist. Creating." % name)
            param = ParameterName(name=name,schema=schema,data_type=paramtype)
            param.save()
        return param
    
    def _save_party_refs(self,  party, party_relation):
        """ Save party and party relation information as parameters on the 
            experiment
        """
        namespace = "http://rmit.edu.au/rif-cs/party/1.0/"
        logger.debug("saving party")
        schema = None
        try:
            schema = Schema.objects.get(
                namespace__exact=namespace)
        except Schema.DoesNotExist:
            logger.debug('Schema ' + namespace +
            ' does not exist. Creating.')
            schema = Schema(namespace=namespace)
            schema.save()
        exp = Experiment.objects.get(pk=self.experiment_id)    
        party_id_param = self._make_param(schema=schema, 
                                          name="party_id",
                                          paramtype=ParameterName.NUMERIC)
        relation_param = self._make_param(schema=schema, 
                                          name="relationtocollection_id",
                                          paramtype=ParameterName.STRING)                    
        parameterset = ExperimentParameterSet(schema=schema, experiment=exp)
        parameterset.save()    
        ep = ExperimentParameter.objects.filter(name=party_id_param,
            parameterset=parameterset,
            parameterset__experiment=exp)
        for p in ep:
            p.delete()
        ep = ExperimentParameter(
            parameterset=parameterset,
            name=party_id_param,
            numerical_value=party.pk)
        ep.save()                        
        ep = ExperimentParameter.objects.filter(name=relation_param,
            parameterset=parameterset,
            parameterset__experiment=exp)
        for p in ep:
            p.delete()
        ep = ExperimentParameter(
            parameterset=parameterset,
            name=relation_param,
            string_value=party_relation)
        ep.save()
   
    def get_profile(self):
        """
        Retrieve existing rif-cs profile for experiment, if any
        """

        ep = ExperimentParameter.objects.filter(name__name='profile',
        parameterset__schema__namespace='http://monash.edu.au/rif-cs/profile/',
        parameterset__experiment__id=self.experiment_id)

        if len(ep):
            return ep[0].string_value
        else:
            return None
