import StarFile

from datetime import datetime

from django.conf import settings

from tardis.tardis_portal.models import Schema, Experiment, Dataset,\
    ExperimentParameter, ExperimentParameterSet,\
    DatasetParameter, DatasetParameterSet,\
    ParameterName

from utils import PDBCifHelper

def update_publication_records():
    populate_pdb_pub_records()


def populate_pdb_pub_records():
    # Identify all publications that conain PDB info
    PDB_SCHEMA = settings.PDB_PUBLICATION_SCHEMA_ROOT
    # use this list comprehension to make sure that the exp. is a publication
    # but not a publication draft.
    publications = [p for p in Experiment.objects\
                    .filter(experimentparameterset__schema__namespace=PDB_SCHEMA)\
                    if p.is_publication() and not p.is_publication_draft()]

    PUB_SCHEMA = settings.PUBLICATION_SCHEMA_ROOT
    last_update_parameter_name = ParameterName.objects.get(name='pdb-last-sync',
                                                           schema__namespace=PUB_SCHEMA)

    def add_if_missing(parameterset, name, string_value=None, numerical_value=None, datetime_value=None):
        try:
            param = ExperimentParameter.objects.get(name__name=name, parameterset=parameterset)
        except ExperimentParameter.DoesNotExist:
            param_name = ParameterName.objects.get(name=name, schema=parameterset.schema)
            param = ExperimentParameter(name=param_name,
                                        parameterset=parameterset)
            param.string_value = string_value
            param.numerical_value = numerical_value
            param.datetime_value = datetime_value
            param.save()

    for pub in publications:
        needs_update = False
        try:
            # try to get the last update time for the PDB data
            pdb_last_update_parameter = ExperimentParameter.objects.get(
                parameterset__schema__namespace=PUB_SCHEMA,
                name=last_update_parameter_name,
                parameterset__experiment=pub
            )
            last_update = pdb_last_update_parameter.datetime_value
            needs_update = last_update + settings.PDB_REFRESH_INTERVAL < datetime.now()

        except ExperimentParameter.DoesNotExist:
            # if the PDB last update time parameter doesn't exist,
            # we definitely need to update the data and create a last
            # update entry
            needs_update = True

            # Check if there are currently any publication parameter sets
            # attached.
            pub_parameter_set = ExperimentParameterSet.objects.filter(schema__namespace=PUB_SCHEMA,
                                                                      experiment=pub)
            # If not, create one...
            if parameter_set.count() == 0:
                parameter_set = ExperimentParameterSet(schema=Schema.objects.get(namespace=PUB_SCHEMA),
                                                       experiment=pub)
                parameter_set.save()
            # If so, use the first (and in theory, only) one ...
            else:
                parameter_set = parameter_set[0]

            pdb_last_update_parameter = None


        # If an update needs to happen...
        if needs_update:
            # 1. get the PDB info
            pdb_parameter_set = ExperimentParameterSet.objects.get(
                schema__namespace=settings.PDB_PUBLICATION_SCHEMA_ROOT,
                experiment=pub)
            pdb = ExperimentParameter.objects.get(name__name='pdb-id',
                                                  parameterset=pdb_parameter_set)
            pdb_id = pdb.string_value
            # 1a. cosmetic change of case for PDB ID, if entered incorrectly
            if pdb_id != pdb_id.upper():
                pdb.string_value = pdb_id.upper()
                pdb.save()

            try:
                # 2. fetch the info from pdb.org
                pdb = PDBCifHelper(pdb_id)

                # 3. insert all standard pdb parameters
                add_if_missing(pdb_parameter_set, 'url', string_value=pdb.get_pdb_url())
                add_if_missing(pdb_parameter_set, 'resolution', numerical_value=pdb.get_resolution())
                add_if_missing(pdb_parameter_set, 'r-value', numerical_value=pdb.get_obs_r_value())
                add_if_missing(pdb_parameter_set, 'r-free', numerical_value=pdb.get_free_r_value())
                add_if_missing(pdb_parameter_set, 'space-group', string_value=pdb.get_spacegroup())
                add_if_missing(pdb_parameter_set, 'unit-cell', string_value=pdb.get_unit_cell())

                # 4. insert sequence info (lazy checking)
                pdb_seq_parameter_sets = ExperimentParameterSet.objects.filter(
                    schema__namespace=settings.PDB_SEQUENCE_PUBLICATION_SCHEMA,
                    experiment=pub)
                if pdb_seq_parameter_sets.count() == 0:
                    # insert seqences
                    for seq in pdb.get_sequence_info():
                        seq_parameter_set = ExperimentParameterSet(
                            schema=Schema.objects.get(
                                namespace=settings.PDB_SEQUENCE_PUBLICATION_SCHEMA),
                            experiment=pub)
                        seq_parameter_set.save()
                        add_if_missing(seq_parameter_set, 'organism', string_value=seq['organism'])
                        add_if_missing(seq_parameter_set, 'expression-system', string_value=seq['expression_system'])
                        add_if_missing(seq_parameter_set, 'sequence', string_value=seq['sequence'])

                # 5. insert/update citation info (aggressive)
                ExperimentParameterSet.objects.filter(
                    schema__namespace=settings.PDB_CITATION_PUBLICATION_SCHEMA,
                    experiment=pub).delete()
                for citation in pdb.get_citations():
                    cit_parameter_set = ExperimentParameterSet(
                        schema=Schema.objects.get(namespace=settings.PDB_CITATION_PUBLICATION_SCHEMA),
                        experiment=pub)
                    cit_parameter_set.save()
                    add_if_missing(cit_parameter_set, 'title', string_value=citation['title'])
                    add_if_missing(cit_parameter_set, 'authors', string_value='; '.join(citation['authors']))
                    add_if_missing(cit_parameter_set, 'journal', string_value=citation['journal'])
                    add_if_missing(cit_parameter_set, 'volume', string_value=citation['volume'])
                    add_if_missing(cit_parameter_set, 'page-range', string_value='-'.join([citation['page_first'], citation['page_last']]))
                    add_if_missing(cit_parameter_set, 'doi', string_value='http://dx.doi.org/'+citation['doi'])
                
            except StarFile.StarError:
                continue # PDB is either unavailable or invalid (maybe notify the user somehow?)
            
            # Set the last update parameter to be now
            if pdb_last_update_parameter == None:
                pdb_last_update_parameter = ExperimentParameter(name=last_update_parameter_name,
                                                                parameterset=pub_parameter_set,
                                                                datetime_value=datetime.now())
            else:
                pdb_last_update_parameter.datetime_value = datetime.now()
            pdb_last_update_parameter.save()

