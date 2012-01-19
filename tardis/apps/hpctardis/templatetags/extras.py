


from django.template import Library
from django import template

    
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import ExperimentParameterSet
from tardis.tardis_portal.models import ExperimentParameter
from tardis.apps.hpctardis.models import PublishAuthorisation
from tardis.apps.hpctardis.models import ActivityPartyRelation
from tardis.apps.hpctardis.models import PartyLocation
from tardis.apps.hpctardis.models import PartyDescription
from tardis.apps.hpctardis.models import ActivityLocation
from tardis.apps.hpctardis.models import ActivityDescription

def party_info(exp,name):
    namespace = "http://rmit.edu.au/rif-cs/party/1.0/"
    try:
        schema = Schema.objects.get(
            namespace__exact=namespace)
    except Schema.DoesNotExist:
        return [("noschema","noschema")]
    
    try:
        parametersets = \
             ExperimentParameterSet.objects.filter(\
                                schema=schema,
                                experiment=exp)

    except ExperimentParameterSet.DoesNotExist, e:
        return [("noparamset","noparamset")]
     
    res = []
    for ps in parametersets:
         
        try:
            params = ExperimentParameter.objects.filter(parameterset = ps,
                                               parameterset__experiment=exp)
        except ExperimentParameter.DoesNotExist, e:
            return []
            
            
        pres = ["UnknownParty","UnknownRelation"]     
        for p in params:
            if p.name.name=='party_id':
                pres[0] = int(p.numerical_value)
            if p.name.name =='relationtocollection_id':
                pres[1] = p.string_value
        res.append(pres)
            
             
    return res
    
    
def activity_info(exp,name):  
    collection_activities_relations = PublishAuthorisation.objects.filter(
                                experiment=exp,
                                status=PublishAuthorisation.APPROVED_PUBLIC)
    res = []
    for collection_activities_relation in collection_activities_relations:
        res.append((collection_activities_relation.activity_record.id,
                   "isOutputOf"))
    return res

    
def party_for_act(act,name):
    
    activity_parties = ActivityPartyRelation.objects.filter(activity=act)
    
    res = []
    for activity_party in activity_parties:
        res.append((activity_party.party.id,
                   activity_party.relation))
    return res

    
def location_for_party(party,type):
    
    locations = PartyLocation.objects.filter(party=party,type=type)
    
    
    if locations:
        res = locations[0].value
        return res
    else:
        return None
    return res

    
        
def location_for_activity(activity,type):
    
    locations = ActivityLocation.objects.filter(activity=activity,type=type)
    
    
    if locations:
        res = locations[0].value
        return res
    else:
        return None
    return res

    
def descs_for_party(party,name):
    
    descs = PartyDescription.objects.filter(party=party)
    return descs
    
    
def descs_for_activity(party,name):
    
    descs = ActivityDescription.objects.filter(party=party)
    return descs

def strip(name):
    return name.strip()    
    
register = template.Library()
register.filter('partyinfo',party_info)
register.filter('activityinfo',activity_info)
register.filter('partyforact',party_for_act)
register.filter('locationforparty',location_for_party)
register.filter('locationforactivity',location_for_activity)
register.filter('descsforparty',descs_for_party)
register.filter('descsforactivity',descs_for_activity)
register.filter('strip',strip)
