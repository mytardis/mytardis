import CifFile
import urllib

class CifHelper:
    def __init__(self, cif_url):
        self.cf = CifFile.ReadCif(cif_url)

    def get_cif_file_object(self):
        return self.cf

    def _is_list(self, obj):
        return isinstance(obj, list)

    def as_list(self, obj):
        return obj if self._is_list(obj) else [obj]

class PDBCifHelper(CifHelper):
    def __init__(self, pdb_id):
        CifHelper.__init__(self, 'http://pdb.org/pdb/files/'+urllib.quote(pdb_id)+'.cif')
        self.pdb_id = pdb_id

    def __getitem__(self,key):
        return CifHelper.get_cif_file_object(self)[self.pdb_id][key]

    def get_pdb_id(self):
        return self['_entry.id']

    def get_pdb_url(self):
        return 'http://pdb.org/pdb/search/structidSearch.do?structureId='+urllib.quote(self.get_pdb_id())

    def get_obs_r_value(self):
        return float(self['_refine.ls_R_factor_obs'])

    def get_free_r_value(self):
        return float(self['_refine.ls_R_factor_R_free'])

    def get_resolution(self):
        return float(self['_reflns.d_resolution_high'])

    def get_spacegroup(self):
        return self['_symmetry.space_group_name_H-M']

    def get_unit_cell(self):
        length_a = self['_cell.length_a']
        length_b = self['_cell.length_b']
        length_c = self['_cell.length_c']
        angle_a = self['_cell.angle_alpha']
        angle_b = self['_cell.angle_beta']
        angle_c = self['_cell.angle_gamma']
        return '(a = %s, b = %s, c = %s),(a = %s, b = %s, c = %s)' % (length_a, length_b, length_c, angle_a, angle_b, angle_c)

    def get_citations(self):
        ids = self.as_list(self['_citation.id'])
        titles = self.as_list(self['_citation.title'])
        journals = self.as_list(self['_citation.journal_abbrev'])
        volumes = self.as_list(self['_citation.journal_volume'])
        pages_first = self.as_list(self['_citation.page_first'])
        pages_last = self.as_list(self['_citation.page_last'])
        years = self.as_list(self['_citation.year'])
        dois = self.as_list(self['_citation.pdbx_database_id_DOI'])
        author_citation_ids = self.as_list(self['_citation_author.citation_id'])
        author_citation_names = self.as_list(self['_citation_author.name'])

        citations = []
        for pub_id, title, journal, volume, page_first, page_last, year, doi in \
            zip(ids, titles, journals, volumes, pages_first, pages_last, years, dois):
            citation = {'_id': pub_id,
                        'title': title,
                        'journal': journal,
                        'volume': volume,
                        'page_first': page_first,
                        'page_last': page_last,
                        'year': year,
                        'doi': doi}
            
            authors = []
            for auth_pub_id, auth_name in zip(author_citation_ids, author_citation_names):
                if auth_pub_id == pub_id:
                    authors.append(auth_name)
            citation['authors'] = authors
            citations.append(citation)

        return citations
        
    def get_sequence_info(self):
        seqs_id = self.as_list(self['_entity_src_gen.entity_id'])
        seqs_org = self.as_list(self['_entity_src_gen.pdbx_gene_src_scientific_name'])
        seqs_exp_sys = self.as_list(self['_entity_src_gen.pdbx_host_org_scientific_name'])

        seqs_code_id = self.as_list(self['_entity_poly.entity_id'])
        seqs_code = self.as_list(self['_entity_poly.pdbx_seq_one_letter_code'])

        seqs_name_id = self.as_list(self['_entity_name_com.entity_id'])
        seqs_name = self.as_list(self['_entity_name_com.name'])

        sequences = []
        for seq_id, seq_org, seq_exp_sys in zip(seqs_id, seqs_org, seqs_exp_sys):
            seq = {'organism': seq_org,
                   'expression_system': seq_exp_sys}

            for seq_name_id, seq_name in zip(seqs_name_id, seqs_name):
                if seq_name_id == seq_id:
                    seq['name'] = seq_name
                    break

            for seq_code_id, seq_code in zip(seqs_code_id, seqs_code):
                if seq_code_id == seq_id:
                    seq['sequence'] = seq_code #.replace(' ', '').replace('\n','')
                    break

            sequences.append(seq)

        return sequences
