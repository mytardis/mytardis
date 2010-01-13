from tardis.tardis_portal.models import Experiment, Author, XML_data, XSLT_docs, Dataset_File, Dataset, Pdbid, Citation, Schema, ParameterName, DatafileParameter, DatasetParameter, Author_Experiment
from django.contrib import admin

admin.site.register(XML_data)
admin.site.register(XSLT_docs)
admin.site.register(Experiment)
admin.site.register(Author)
admin.site.register(Dataset)
admin.site.register(Dataset_File)
admin.site.register(Pdbid)
admin.site.register(Citation)
admin.site.register(Schema)
admin.site.register(ParameterName)
admin.site.register(DatafileParameter)
admin.site.register(DatasetParameter)
admin.site.register(Author_Experiment)