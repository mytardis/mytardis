from django.db import models


# Create your models here.
   
class PartyRecord(models.Model):
    key = models.CharField(max_length=200)
    type = models.CharField(max_length=80)
    name_title = models.CharField(max_length=200)
    name_given = models.CharField(max_length=200)
    name_family = models.CharField(max_length=200)
    location = models.CharField(default="",max_length=200)
    description = models.TextField(default="",blank=True)
    
    def __unicode__(self):
        return u"%s %s %s: %s" % (self.name_title, self.name_given, 
                                  self.name_family, self.location)  
    
    def get_fullname(self):
        return u'%s %s %s' % (self.name_title,self.name_given,self.name_family)
    
class ActivityRecord(models.Model):
    key = models.CharField(default="",max_length=200)
    type = models.CharField(default="",max_length=80)
    name = models.CharField(default="",max_length=200)
    description = models.TextField(default="",blank=True)
    parties = models.ManyToManyField(PartyRecord,through="ActivityPartyRelation")
    
    
    
    def __unicode__(self):
        return u"%s" % (self.name)  

class ActivityPartyRelation(models.Model):
    activity = models.ForeignKey(ActivityRecord)
    party = models.ForeignKey(PartyRecord)
    relation = models.CharField(max_length=80,default="isManagedBy")
    