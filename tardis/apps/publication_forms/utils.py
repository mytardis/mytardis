import CifFile
import urllib

class CifHelper:
    def __init__(self, cif_url):
        self.cf = CifFile.ReadCif(cif_url)

    def get_cif_file_object(self):
        return self.cf


class PDBCifHelper(CifHelper):
    def __init__(self, pdb_id):
        CifHelper.__init__(self, 'http://pdb.org/pdb/files/'+urllib.quote(pdb_id)+'.cif')
        self.pdb_id = pdb_id

    def __getitem__(self,key):
        return CifHelper.get_cif_file_object(self)[self.pdb_id][key]
