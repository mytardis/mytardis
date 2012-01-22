from django.db import models
from django.conf import settings
from tardis.tardis_portal.models import Experiment


class NameParts(models.Model):
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
    type = models.CharField(default="url",
                            choices=(('email','email'),('postaladdress','postaladdress')
                                                        ),max_length=80,help_text="email, postaladdress")
    value = models.TextField(default="",blank=True)
    party = models.ForeignKey(PartyRecord)
    
    def __unicode__(self):
        return u"%s:%s" % (self.type, self.value)  
    
    
class PartyDescription(models.Model):
    type = models.CharField(default="",          
          choices=(('brief','brief'),('full','full'),('logo','logo'),('note','note')),
          max_length=80,help_text="brief,full,logo,note")
    value = models.TextField(default="",blank=True)
    party = models.ForeignKey(PartyRecord)
    
    def __unicode__(self):
        return u"%s:%s" % (self.type, self.value)
        
    
class ActivityRecord(models.Model):
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
    type = models.CharField(default="",
                            choices=(('brief','brief'),('full','full'),('logo','logo'),('note','note')),
                            max_length=80,help_text="brief,full,logo,note")
    value = models.TextField(default="",blank=True)
    party = models.ForeignKey(ActivityRecord,help_text="The party")
    
    def __unicode__(self):
        return u"%s:%s" % (self.type, self.value)
        
        
class ActivityLocation(models.Model):
    type = models.CharField(default="url",max_length=80)
    value = models.TextField(default="",blank=True)
    activity = models.ForeignKey(ActivityRecord)
    
class ActivityPartyRelation(models.Model):
    activity = models.ForeignKey(ActivityRecord,help_text="The source activity")
    party = models.ForeignKey(PartyRecord,help_text="The destination party")
    relation = models.CharField(max_length=80,
                                default="isManagedBy",
                                choices=(('isFundedBy','isFundedBy'),('isManagedBy','isManagedBy'),
                                                                      ('isOwnedBy','isOwnedBy'),
                                                                      ('hasParticipant','hasParticipant')),
                                help_text="isFundedBy, isManagedBy, isOwnedBy, hasParticipant")
    
    
class PublishAuthorisation(models.Model):
    
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
    
    