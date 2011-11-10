from tardis.tardis_portal.models import ExperimentParameter, ExperimentParameterSet, ParameterName, Schema
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from django.template import Context
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import rifcsprovider

class SchemaRifCsProvider(rifcsprovider.RifCsProvider):
    
    def __init__(self):
        self.namespace = None
        self.sample_desc_schema_ns = None
        self.related_info_schema_ns = settings.RELATED_INFO_SCHEMA_NAMESPACE 
        self.creative_commons_schema_ns = 'http://www.tardis.edu.au/schemas/creative_commons/2011/05/17'
        self.annotation_schema_ns = 'http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07'
        
        
    def is_schema_valid(self, experiment):
        eps = ExperimentParameter.objects.filter(
                                    parameterset__experiment = experiment, 
                                    name__schema__namespace = self.namespace)
        if len(eps) > 0:
            schema = Schema.objects.get(namespace = self.namespace)
            return True
        return False
            
    def get_beamline(self, experiment):    
        sch = Schema.objects.get(namespace=self.namespace)         
        param = ParameterName.objects.get(schema=sch, name='beamline')
        res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
        return res.string_value
   
    def get_investigator_list(self, experiment):
        authors = [a.author for a in experiment.author_experiment_set.all()]
        return "\n*".join(authors)
           
    def get_sample_description_list(self, experiment, beamline):
        sch = Schema.objects.get(namespace=self.sample_desc_schema_ns)
        params = ParameterName.objects.get(schema=sch, name='SampleDescription')
        descriptions = [x.string_value for x in 
                         ExperimentParameter.objects.filter(
                          parameterset__experiment=experiment, name=params)]
        return "\n".join(descriptions)
        
    def get_anzsrcfor_subjectcodes(self, experiment):
        return self._get_param("anzsrcfor_codes", self.annotation_schema_ns, experiment)
 
    def get_local_subjectcodes(self, experiment):
        return self._get_param("local_subject_codes", self.annotation_schema_ns, experiment) 
    
    def get_notes(self, experiment):
        return self._get_param("exp_notes", self.annotation_schema_ns, experiment)
    
    def get_address(self, experiment):    
        return self._get_param("exp_address", self.annotation_schema_ns, experiment)
        
    def get_license_uri(self, experiment):
        return self._get_param("license_uri", self.creative_commons_schema_ns, experiment)
    
    def get_license_title(self, experiment):
        return self._get_param("license_name", self.creative_commons_schema_ns, experiment)

    def get_related_info_list(self, experiment):
        related_info_dicts = []
        # Get all the titles, notes and urls belonging to that experiment
        sch = Schema.objects.get(namespace=self.related_info_schema_ns)         
        exp_params = ExperimentParameter.objects.filter(name__schema=sch, parameterset__experiment=experiment)
        selected_values = exp_params.values('parameterset__id', 'string_value', 'name__name')
        
        # Get the list of unique parameterset ids in the param set
        ids = [x['parameterset__id'] for x in selected_values]
        uniq_ids = list(set(ids))
        
        for id in uniq_ids:
            # Get the title, notes and url belonging to a specific parameter set 
            related_info_params = [x for x in selected_values if x['parameterset__id'] == id]
            related_info_dicts.append(self._create_related_info_dict(related_info_params))
        
        return related_info_dicts
        
    def _create_related_info_dict(self, related_info_params):
        dict= {}
        for x in related_info_params:
            dict[x['name__name']] = x['string_value']
        return dict
    
    def get_rifcs_context(self, experiment):
        c = Context({})
        beamline = self.get_beamline(experiment)
        c['experiment'] = experiment
        c['beamline'] = self.get_beamline(experiment)
        c['sample_description_list'] = self.get_sample_description_list(experiment, beamline)
        c['investigator_list'] = self.get_investigator_list(experiment)
        c['license_title'] = self.get_license_title(experiment)
        c['license_uri'] = self.get_license_uri(experiment)
        return c
        
    def _get_param(self, key, namespace, experiment):
        parameterset = ExperimentParameterSet.objects.filter(
                            schema__namespace=namespace,
                            experiment__id=experiment.id)
        if len(parameterset) > 0:
            psm = ParameterSetManager(parameterset=parameterset[0])
            try:
                return psm.get_param(key, True)
            except MultipleObjectsReturned:
                return psm.get_params(key, True)
            except ObjectDoesNotExist:
                return None
    