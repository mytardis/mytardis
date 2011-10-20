from tardis.tardis_portal.models import ExperimentParameter, ParameterName, Schema
    
ANSTO_BEAMLINES = ["echidna", "wombat", "quokka", "kowari", "platypus"]
SYNCHROTRON_BEAMLINES = ["IR", "MX", "SAX"]
    
    
def get_beamline_email(beamline):
    if beamline in ANSTO_BEAMLINES:
        return "%s@ansto.gov.au" % beamline
    elif beamline in SYNCHROTRON_BEAMLINES:
        return "%s@synchrotron.gov.au" % beamline
    
def get_beamline(experiment):    
    sch = Schema.objects.get(namespace='http://www.tardis.edu.au/schemas/as/experiment/2010/09/21')
    param = ParameterName.objects.get(schema=sch, name='beamline')
    res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
    return res.string_value

def get_originating_source(beamline):
    if beamline in ANSTO_BEAMLINES:
        return "http://mecat-test.nbi.ansto.gov.au:8080/oai/provider"
    elif beamline in SYNCHROTRON_BEAMLINES:
        return "http://tardis.synchrotron.org.au/oai/provider"
    
def get_key(experiment, beamline):
    exp_id = experiment.id
    if beamline in ANSTO_BEAMLINES:
        return "mecat-test.nbi.ansto.gov.au:8080/experiment/%s" % exp_id
    elif beamline in SYNCHROTRON_BEAMLINES:
        return "tardis.synchrotron.org.au/experiment/%s" % exp_id
    
def get_institution(beamline):
    if beamline in ANSTO_BEAMLINES:
        return "ANSTO"
    elif beamline in SYNCHROTRON_BEAMLINES:
        return "Synchrotron"    

def get_sample_description_list(experiment, beamline):
    return "blah\nblah\nblah"

def get_investigator_list(experiment):
    return "*me\n*me\n*me"