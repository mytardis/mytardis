


import logging

from django.template import Library
from django import template

    
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import ExperimentParameterSet
from tardis.tardis_portal.models import ExperimentParameter
from tardis.apps.hpctardis.models import PublishAuthorisation
from tardis.apps.hpctardis.models import ActivityPartyRelation
from tardis.apps.hpctardis.models import PartyLocation
from tardis.apps.hpctardis.models import PartyRecord
from tardis.apps.hpctardis.models import PartyDescription
from tardis.apps.hpctardis.models import ActivityLocation
from tardis.apps.hpctardis.models import ActivityDescription



logger = logging.getLogger(__name__)



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
                try:
                    party_record = PartyRecord.objects.get(pk=p.numerical_value)
                except PartyRecord.DoesNotExist, e:
                    pass
                else:
                    pres[0] = party_record.key
                #pres[0] = int(p.id)
            if p.name.name =='relationtocollection_id':
                pres[1] = p.string_value
        res.append(pres)
            
             
    return res
    
    
def activity_info(exp,name):  
    collection_activities_relations = PublishAuthorisation.objects.filter(
                                experiment=exp,
                                status=PublishAuthorisation.APPROVED_PUBLIC).order_by('activity_record__key')
    res = []
    for collection_activities_relation in collection_activities_relations:
        res.append((collection_activities_relation.activity_record.key,
                   "isOutputOf"))
    return res

    
def party_for_act(act,name):
    
    activity_parties = ActivityPartyRelation.objects.filter(activity=act).order_by('activity__key')
    
    res = []
    for activity_party in activity_parties:
        res.append((activity_party.party.key,
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


def make_list(string):    
    res = string.split(',')
    return res    
    
    

def breakup_desc(exp):
    """ Breaks up exp description into tuple containing brief desc, full
        description and list of links
    """
    from tardis.apps.hpctardis.publish.rif_cs_profile.rif_cs_PublishProvider import paragraphs
    import re
    paras = paragraphs(str(exp.description))
    output = [x for x in paras]
    if len(output):    
        brief = output[0]
    else:
        return []        
    regex = re.compile("^([^\:]+)\:(.*)\n")
    links = []
    full = []
    for link_or_full_desc in output[1:]:
        logger.debug("link_or_full_desc=%s" % repr(link_or_full_desc))
        link = regex.match(link_or_full_desc)
        if link:
            link_groups = link.groups()
            logger.debug("link_groups=%s" % repr(link_groups))
            logger.debug("len(link_groups)=%s" % len(link_groups))
            if len(link_groups) == 2:                
                (link_type,url) = link_groups
                match_end = link.end()
                desc = link_or_full_desc[match_end:]
                logger.debug("desc=%s" % repr(desc))
                links.append((link_type, url, desc))
                continue
        full.append(link_or_full_desc)
    joined_full = "\n\n".join(full)
    res = ((brief, links, (joined_full,)),)
    return res
    
   
    
register = template.Library()
register.filter('partyinfo',party_info)
register.filter('activityinfo',activity_info)
register.filter('partyforact',party_for_act)
register.filter('locationforparty',location_for_party)
register.filter('locationforactivity',location_for_activity)
register.filter('descsforparty',descs_for_party)
register.filter('descsforactivity',descs_for_activity)
register.filter('strip',strip)
register.filter('makelist',make_list)
register.filter('breakupdesc',breakup_desc)
