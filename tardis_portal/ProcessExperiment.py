#
# Copyright (c) 2010, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
from tardis.tardis_portal.models import *
from tardis.tardis_portal.ExperimentParser import ExperimentParser
from django.utils.safestring import SafeUnicode
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
			
	def register_experiment_xmldata(self, xmldata, created_by):

			xmlString = xmldata
			url = "http://www.example.com"
			self.url = "http://www.example.com"

			ep = ExperimentParser(str(xmlString))

			e = Experiment(url=url, approved=True, \
			title=ep.getTitle(), institution_name=ep.getAgentName("DISSEMINATOR"), \
			description=ep.getAbstract(), created_by=created_by)

			e.save()

			self.process_METS(e, ep)

			return e.id
			
	def register_experiment_xmldata_file(self, filename, created_by, expid=None):

		f = open(filename, "r")
		xmlString = f.read()
		f.close()

		url = "http://www.example.com"
		self.url = "http://www.example.com"

		ep = ExperimentParser(str(xmlString))
		
		del xmlString

		e = Experiment(id=expid, url=url, approved=True, \
		title=ep.getTitle(), institution_name=ep.getAgentName("DISSEMINATOR"), \
		description=ep.getAbstract(), created_by=created_by)

		e.save()

		self.process_METS(e, ep)

		del ep

		import gc
		gc.collect()			

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
			
					try:
			
						schema = Schema.objects.get(namespace__exact=xmlns)

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
								
					except Schema.DoesNotExist:						
						print "Schema " + xmlns + " doesn't exist!"
						#todo replace with logging
		
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
			
					try:
						schema = Schema.objects.get(namespace__exact=xmlns)
					

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
							
					except Schema.DoesNotExist:	
						xml_data = XML_data(datafile=datafile, xmlns=SafeUnicode(xmlns), data=SafeUnicode(techxml.getvalue()))
						xml_data.save()