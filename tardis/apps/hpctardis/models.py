# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, RMIT e-Research Office
#   (RMIT University, Australia)
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

from django.db import models
from django.conf import settings
from tardis.tardis_portal.models import Experiment

class NameParts(models.Model):
    """ The component parts of a name used in parties and activities
        
    """
    title = models.CharField(max_length=200,default="",blank=True,help_text="For example, Mr")
    given = models.CharField(max_length=200,default="",blank=True,help_text="For example, Joe")
    family = models.CharField(max_length=200,default="",blank=True,help_text="For example, Bloggs")
    suffix = models.CharField(max_length=200,default="",blank=True,help_text="For example, OBE")
    
    def __unicode__(self):
        return u' '.join((self.title,self.given,
                          self.family,self.suffix)).strip()
                          
                          
    class Meta:
        verbose_name_plural = "Names"


class PartyRecord(models.Model):
    """ A record for an ANDS party
        
        :attribute key: the full ANDS URI identifier
        :attribute type: the designation of the type of party
        :attribute partyname: the nameparts representation of the party name
        
        :attribute repos: a foreign key to the class :class:`smra.smra_portal.models.Repository`
        :attribute schemas: a many-to-many key to the class :class:`smra.smra_portal.models.Schema` via class :class:`smra.smra_portal.models.MediaObjectParameterSet`        
        
    """
    key = models.CharField(max_length=200,help_text="The full ANDS URI identifier")
    type = models.CharField(max_length=80,
                            default="person",
                            choices=(('person','person'),('group','group'),('administrativePosition','administrativePosition')),
                            help_text="The ANDS party type (person, group, or administrativePosition)")
    partyname = models.ForeignKey(NameParts,related_name="reverse",help_text="The nameof the party")
    birthdate = models.DateField(null=True,blank=True,help_text="Leave blank if not appropriate")
    deathdate = models.DateField(null=True,blank=True,help_text="Leave blank if not appropriate")
    #altname = models.ForeignKey(NameParts,blank=True,null=True,related_name="reverse")
    subject = models.CharField(max_length=200,default="",blank=True,help_text="Comma delimited list of subject names or codes")
    
    def __unicode__(self):
        return u"%s" % self.partyname
        
    def get_full_record(self):
        locations = PartyLocation.objects.filter(party__pk=self.pk)
        descriptions = PartyDescription.objects.filter(party__pk=self.pk)
        return u"%s %s %s" % (self.partyname, 
                                    u' '.join([ unicode(x) for x in locations]),
                                    u' '.join([ unicode(x) for x in descriptions])
                                     )  
    
    def get_email_addresses(self):
        party_locs = PartyLocation.objects.filter(party=self,
                                type="email").values_list('value',flat=True)
        return party_locs
    
    def get_fullname(self):
        return self.partyname
    
class PartyLocation(models.Model):
    """ A location for a party
        
        :attribute type: ANDS designation of type of location
        :attribute value: the value for the location
        :attribute party: the party that the location is associated with
    """

    type = models.CharField(default="url",
                            choices=(('email','email'),('postaladdress','postaladdress')
                                                        ),max_length=80,help_text="email, postaladdress")
    value = models.TextField(default="",blank=True)
    party = models.ForeignKey(PartyRecord)
    
    def __unicode__(self):
        return u"%s:%s" % (self.type, self.value)  
    
    
class PartyDescription(models.Model):
    """ A description for a party
        
        :attribute type: ANDS designation of type of description
        :attribute value: the value for the description
        :attribute party: the party that the location is associated with
    """

    type = models.CharField(default="",          
          choices=(('brief','brief'),('full','full'),('logo','logo'),('note','note')),
          max_length=80,help_text="brief,full,logo,note")
    value = models.TextField(default="",blank=True)
    party = models.ForeignKey(PartyRecord)
    
    def __unicode__(self):
        return u"%s:%s" % (self.type, self.value)
        
    
class ActivityRecord(models.Model):
    """ A record for an ANDS activity
        
        :attribute key: the full ANDS URI identifier        
        :attribute indent: an additional ANDS URI identifier
        :attribute type: the designation of the type of party
        :attribute activityname: the nameparts representation of the activity name
        :attribute description: deprecated, do not use.
        :attribute parties: the associated parties for this activity
        :attribute subject: comma delimited list of subject names or codes
        :attribute group: the origin of the activity
        
    """
    ident = models.CharField(default="",max_length=200,blank=True)
    key = models.CharField(default="",max_length=200,help_text="The full ANDS identifier")
    type = models.CharField(default="",
                            choices=(('project','project'),('program','program'),('course','course'),('award','award'),('event','event')),
                            max_length=80,
                            help_text="project, program, course, award, event")
    activityname = models.ForeignKey(NameParts,help_text="The name of the activity")
    description = models.TextField(default="",blank=True,help_text="Deprecated.  Do not use")
    parties = models.ManyToManyField(PartyRecord,
                                     through="ActivityPartyRelation")
    subject = models.CharField(max_length=200,default="",blank=True,
                               help_text="comma delimited list of subjects names or codes")
    group = models.CharField(max_length=200,blank=True, default=settings.GROUP,
                             help_text="The origin of the activity")
    
    def __unicode__(self):
        return u"%s" % (self.activityname)  

        
class ActivityDescription(models.Model):
    """ A description for a activity
        
        :attribute type: ANDS designation of type of description
        :attribute value: the value for the description
        :attribute party: the party that the location is associated with
    """
    
    type = models.CharField(default="",
                            choices=(('brief','brief'),('full','full'),('logo','logo'),('note','note')),
                            max_length=80,help_text="brief,full,logo,note")
    value = models.TextField(default="",blank=True)
    party = models.ForeignKey(ActivityRecord,help_text="The party")
    
    def __unicode__(self):
        return u"%s:%s" % (self.type, self.value)
        
        
class ActivityLocation(models.Model):
    """ A location for a activity
        
        :attribute type: ANDS designation of type of location
        :attribute value: the value for the location
        :attribute activity: the activity that the location is associated with
    """
    
    type = models.CharField(default="url",max_length=80)
    value = models.TextField(default="",blank=True)
    activity = models.ForeignKey(ActivityRecord)
    
class ActivityPartyRelation(models.Model):
    """ The relation between an activity and a party 
       :attribute activity: the source
       :attribute party: the destination
       :attribute relation: the relationship between the above
    """
    activity = models.ForeignKey(ActivityRecord,help_text="The source activity")
    party = models.ForeignKey(PartyRecord,help_text="The destination party")
    relation = models.CharField(max_length=80,
                                default="isManagedBy",
                                choices=(('isFundedBy','isFundedBy'),('isManagedBy','isManagedBy'),
                                                                      ('isOwnedBy','isOwnedBy'),
                                                                      ('hasParticipant','hasParticipant')),
                                help_text="isFundedBy, isManagedBy, isOwnedBy, hasParticipant")
    
    
class PublishAuthorisation(models.Model):
    """ Information of authorisation of collection to authoriser party
        
        :attribute auth_key: the crypto key used for identifying authorisers replies
        :attribute experiment: the collection to be authorised
        :attribute authoriser: the full name of the authoriser
        :attribute email: the email address of the authoriser
        :attribute status: the state of the experiment publication
        :attribute party_record: the authorising party
        :attribute activity_record: the activity the authoriser represents
        
    """
    PRIVATE = 0
    PENDING_APPROVAL = 1
    APPROVED_PUBLIC = 2
    EXPIRED=3
    
    _STATUS_TYPES = (
                     (PRIVATE,'Private'),
                     (PENDING_APPROVAL,'Pending Approval'),
                     (APPROVED_PUBLIC,'Approved Public'),
                     (EXPIRED,'Expired')
                     )
    auth_key = models.CharField(max_length=80)
    experiment = models.ForeignKey(Experiment)
    authoriser =  models.TextField(default="")
    email = models.EmailField()
    status = models.IntegerField(choices=_STATUS_TYPES, default=PRIVATE)
    party_record = models.ForeignKey(PartyRecord,blank= True, null=True)
    activity_record = models.ForeignKey(ActivityRecord, blank = True, null = True)
    
    def _get_status_string(self):
        return self._STATUS_TYPES[self.status][1]
    
    def __unicode__(self):
        return u"%s exp=%s auth=%s %s %s %s" % (self._get_status_string(),self.experiment.id,
                        self.authoriser,self.email, self.party_record,
                        self.activity_record)  

class PublishAuthEvent(models.Model):
    publish_auth = models.ForeignKey(PublishAuthorisation)
    type = models.CharField(max_length=200,default="unknown")
    date_authorised = models.DateTimeField(auto_now_add=True)
    
    