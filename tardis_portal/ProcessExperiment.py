from tardis.tardis_portal.models import *
from tardis.tardis_portal.ExperimentParser import ExperimentParser
from django.utils.safestring import SafeUnicode
# from au.edu.tardis.tardis_portal import XslTranslator
import datetime
import urllib

class ProcessExperiment:
	def download_xml(self, url):
		f = urllib.urlopen(url)
		xmlString = f.read()
		
		return xmlString
		
	def null_check(self, string):
		if string == "null":
			return None
		else:
			return string
			
	def register_experiment_xmldata(self, xmldata, created_by, private_password=None, ftp_location=None, ftp_port=None, ftp_username=None, ftp_password=None, experiment_owner=None):

			xmlString = xmldata
			url = "http://www.example.com"
			self.url = "http://www.example.com"

			ep = ExperimentParser(str(xmlString))

			e = Experiment(url=url, approved=False, private_password=private_password , ftp_location=ftp_location , \
			ftp_port=ftp_port , ftp_username=ftp_username, ftp_password=ftp_password , \
			title=ep.getTitle(), institution_name=ep.getAgentName("DISSEMINATOR"), \
			description=ep.getAbstract(), created_by=created_by, experiment_owner=SafeUnicode(experiment_owner))

			e.save()

			self.process_METS(e, ep)

			return e.id
			
	def process_METS(self, e, ep):
		
		url_path = self.url.rpartition('/')[0] + self.url.rpartition('/')[1]
		
		for pdbid in ep.getPDBIDs():
			p = Pdbid(experiment=e, pdbid=SafeUnicode(pdbid))
			p.save()
		
		for citation in ep.getRelationURLs():
			c = Citation(experiment=e, url=SafeUnicode(citation))
			c.save()		
		
		author_experiments = Author_Experiment.objects.all()
		author_experiments = author_experiments.filter(experiment=e).delete()
		
		x = 0
		for authorName in ep.getAuthors():
			author = Author(name=SafeUnicode(authorName))
			author.save()
			author_experiment = Author_Experiment(experiment=e, author=author, order=x)
			author_experiment.save()
			x = x + 1

		e.dataset_set.all().delete()

		for dmdid in ep.getDatasetDMDIDs():
			d = Dataset(experiment=e, description=ep.getDatasetTitle(dmdid))
			d.save()
			for admid in ep.getDatasetADMIDs(dmdid):
				
					techxml = ep.getTechXML(admid)
					prefix = techxml.getroot().prefix
					xmlns = techxml.getroot().nsmap[prefix]					
			
					schema = Schema.objects.get(namespace__exact=xmlns)
					
					if(schema):
						parameternames = ParameterName.objects.filter(schema__namespace__exact=schema.namespace)
						parameternames = parameternames.order_by('id')					
					
						for pn in parameternames:
							
							if pn.is_numeric:
								value = ep.getParameterFromTechXML(techxml, pn.name)

								if value != None:
									dp = DatasetParameter(dataset=d, name=pn, \
									string_value=None, numerical_value=float(value))
									dp.save()
							else:
								dp = DatasetParameter(dataset=d, name=pn, \
								string_value=ep.getParameterFromTechXML(techxml, pn.name), numerical_value=None)
								dp.save()															
							
		
			for fileid in ep.getFileIDs(dmdid):
				
				# if ep.getFileLocation(fileid).startswith('file://'):
				# 					absolute_filename = url_path + ep.getFileLocation(fileid).partition('//')[2]
				# 				else:
				# 					absolute_filename = ep.getFileLocation(fileid)	
				
				if self.null_check(ep.getFileName(fileid)):
					filename = ep.getFileName(fileid)
				else:
					filename = ep.getFileLocation(fileid).rpartition('/')[2]
					
				print filename
				
				datafile=Dataset_File(dataset=d, filename=filename, \
				url=ep.getFileLocation(fileid), size=ep.getFileSize(fileid))
				datafile.save()
				
				for admid in ep.getFileADMIDs(fileid):

					techxml = ep.getTechXML(admid)
					prefix = techxml.getroot().prefix
					xmlns = techxml.getroot().nsmap[prefix]					
			
					schema = Schema.objects.get(namespace__exact=xmlns)
					
					if(schema):
						parameternames = ParameterName.objects.filter(schema__namespace__exact=schema.namespace)					
						parameternames = parameternames.order_by('id')
						
						for pn in parameternames:

							if pn.is_numeric:
								value = ep.getParameterFromTechXML(techxml, pn.name)
								if value != None:
									dp = DatafileParameter(dataset_file=datafile, name=pn, \
									string_value=None, numerical_value=float(value))
									dp.save()
							else:
								dp = DatafileParameter(dataset_file=datafile, name=pn, \
								string_value=ep.getParameterFromTechXML(techxml, pn.name), numerical_value=None)
								dp.save()
					
					else:
						xml_Data = XML_data(datafile=datafile, xmlns=xmlns, data=techxml)
						xml_Data.save()