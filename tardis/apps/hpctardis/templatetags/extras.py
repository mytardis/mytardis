


from django.template import Library
from django import template

    
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import ExperimentParameterSet
from tardis.tardis_portal.models import ExperimentParameter
from tardis.apps.hpctardis.models import PublishAuthorisation
from tardis.apps.hpctardis.models import ActivityPartyRelation

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


    
    
register = template.Library()
register.filter('partyinfo',party_info)
register.filter('activityinfo',activity_info)
register.filter('partyforact',party_for_act)