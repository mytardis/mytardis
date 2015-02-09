from tardis.tardis_portal.models import ExperimentParameter, ExperimentParameterSet, ParameterName, Schema
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager
from django.template import Context
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
#from html2text import html2text

import tardis.apps.ands_register.publishing as publishing
from tardis.apps.ands_register.publishing import PublishHandler

import rifcsprovider

class SchemaRifCsProvider(rifcsprovider.RifCsProvider):

    def __init__(self):
        self.namespace = None
        self.sample_desc_schema_ns = None
        self.related_info_schema_ns = settings.RELATED_INFO_SCHEMA_NAMESPACE
        self.creative_commons_schema_ns = 'http://www.tardis.edu.au/schemas/creative_commons/2011/05/17'
        self.annotation_schema_ns = 'http://www.tardis.edu.au/schemas/experiment/annotation/2011/07/07'

    def can_publish(self, experiment):
        return experiment.public_access != experiment.PUBLIC_ACCESS_NONE

    def is_schema_valid(self, experiment):
        eps = ExperimentParameter.objects.filter(
                                    parameterset__experiment = experiment,
                                    name__schema__namespace = self.namespace)
        return True # TJD: temporary
        # if len(eps) > 0:
        #     schema = Schema.objects.get(namespace = self.namespace)
        #     return True
        # return False

    def get_beamlines(self, experiment):
#        sch = Schema.objects.get(namespace=self.namespace)
#        param = ParameterName.objects.get(schema=sch, name='beamline')
#        res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
#        return res.string_value
        return self._get_params('beamline', self.namespace, experiment)

    def get_proposal_id(self, experiment):
        sch = Schema.objects.get(namespace=self.namespace)
        param = ParameterName.objects.get(schema=sch, name='EPN')
        res = ExperimentParameter.objects.get(parameterset__experiment = experiment, name=param)
        return res.string_value

    def get_description(self, experiment):
        phandler = PublishHandler(experiment.id)
        desc = phandler.custom_description()
        if not desc:
            desc = experiment.description
        return self.format_desc(desc)

    def format_desc(self, desc):
        formatted_desc = desc
        if self._is_html_formatted(desc):
            formatted_desc = html2text(desc)
        return formatted_desc.strip()

    def get_authors(self, experiment):
        phandler = PublishHandler(experiment.id)
        authors = phandler.custom_authors()
        if authors:
            return "* " + "\n* ".join(authors)
        else:
            return self.get_investigator_list(experiment)

    def get_url(self, experiment, server_url):
       """Only public experiments can show the direct link to the experiment
       in the rif-cs"""
       if experiment.public_access != experiment.PUBLIC_ACCESS_NONE:
           return "%s/experiment/view/%s/" % (server_url, experiment.id)

    def get_investigator_list(self, experiment):
        authors = [a.author for a in experiment.experimentauthor_set.all()]
        return "* " + "\n* ".join(authors)

    def get_sample_description_list(self, experiment):
        sch = Schema.objects.get(namespace=self.sample_desc_schema_ns)
        params = ParameterName.objects.get(schema=sch, name='SampleDescription')
        descriptions = [x.string_value for x in
                         ExperimentParameter.objects.filter(
                          parameterset__experiment=experiment, name=params)]
        return "\n".join(descriptions)

    def get_anzsrcfor_subjectcodes(self, experiment):
        return self._get_params("anzsrcfor_codes", self.annotation_schema_ns, experiment)

    def get_local_subjectcodes(self, experiment):
        return self._get_params("local_subject_codes", self.annotation_schema_ns, experiment)

    def get_notes(self, experiment):
        return self._get_params("exp_notes", self.annotation_schema_ns, experiment)

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

    def get_group(self):
        return settings.RIFCS_GROUP

    def get_located_in(self):
        return settings.RIFCS_MYTARDIS_KEY

    def _create_related_info_dict(self, related_info_params):
        dict= {}
        for x in related_info_params:
            dict[x['name__name']] = x['string_value']
        return dict

    def get_rifcs_context(self, experiment):
        c = Context({})
        beamlines = self.get_beamlines(experiment)
        c['blnoun'] = 'beamline'
        c['experiment'] = experiment
        c['beamlines'] = beamlines
        try:
            c['sample_description_list'] = self.get_sample_description_list(experiment)
        except Schema.DoesNotExist:
            pass
        c['investigator_list'] = self.get_authors(experiment)
        c['license_title'] = self.get_license_title(experiment)
        c['license_uri'] = self.get_license_uri(experiment)
        c['description'] = self.get_description(experiment)
        c['anzsrcfor'] = self.get_anzsrcfor_subjectcodes(experiment)
        c['localcodes'] = self.get_local_subjectcodes(experiment)
        c['license_title'] = self.get_license_title(experiment)
        c['license_uri'] = self.get_license_uri(experiment)
        c['address'] = self.get_address(experiment)
        try:
            c['related_info_list'] = self.get_related_info_list(experiment)
        except Schema.DoesNotExist:
            pass
        c['group'] = self.get_group()
        try:
            c['proposal_id'] = self.get_proposal_id(experiment)
        except Schema.DoesNotExist:
            pass
        try:
            c['located_in'] = self.get_located_in()
        except AttributeError:
            pass
        c['rights'] = []
        c['access_rights'] = []
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


    def _get_params(self, key, namespace, experiment):
        parameterset = ExperimentParameterSet.objects.filter(
                            schema__namespace=namespace,
                            experiment__id=experiment.id)
        if len(parameterset) > 0:
            psm = ParameterSetManager(parameterset=parameterset[0])
            return psm.get_params(key, True)
        else:
            return []
