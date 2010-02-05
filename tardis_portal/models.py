from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import SafeUnicode

class XSLT_docs(models.Model):
	xmlns = models.URLField(max_length=400, primary_key=True)
	data = models.TextField()
	
	def __unicode__(self):
		return self.xmlns

class Author(models.Model):
	name = models.CharField(max_length=400, primary_key=True)
	
	def __unicode__(self):
		return self.name

class Experiment(models.Model):
	url = models.URLField(verify_exists=False, max_length=400) #use verify-exists
	approved = models.BooleanField()
	title = models.CharField(max_length=400)
	institution_name = models.CharField(max_length=400)
	description = models.TextField(blank=True)
	update_time = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User)
	handle = models.TextField(null=True, blank=True)
	
	def __unicode__(self):
		return self.title
		
class Experiment_Owner(models.Model):
	experiment = models.ForeignKey(Experiment)
	user = models.ForeignKey(User)
	
	def __unicode__(self):
		return SafeUnicode(self.experiment.id) + " | " + SafeUnicode(self.user.username)
	
class Author_Experiment(models.Model):
	experiment = models.ForeignKey(Experiment)
	author = models.ForeignKey(Author)
	order = models.PositiveIntegerField()

	def __unicode__(self):
		return SafeUnicode(self.author.name) + " | " + SafeUnicode(self.experiment.id) + " | " + SafeUnicode(self.order)
		
class Pdbid(models.Model):
	experiment = models.ForeignKey(Experiment)
	pdbid = models.CharField(max_length=5)

	def __unicode__(self):
		return self.pdbid
		
class Citation(models.Model):
	experiment = models.ForeignKey(Experiment)
	url = models.CharField(max_length=400)

	def __unicode__(self):
		return self.url
		
class Dataset(models.Model):
	experiment = models.ForeignKey(Experiment)
	description = models.TextField()

	def __unicode__(self):
		return self.description	

class Dataset_File(models.Model):
	dataset = models.ForeignKey(Dataset)
	filename = models.CharField(max_length=400)
	url = models.URLField(max_length=400)
	size = models.CharField(blank=True, max_length=400)
	
	def __unicode__(self):
		return self.filename		
		
class Schema(models.Model):
	namespace = models.URLField(verify_exists=False, max_length=400)

	def __unicode__(self):
		return self.namespace
		
class ParameterName(models.Model):
	schema = models.ForeignKey(Schema)
	name = models.CharField(max_length=60)
	full_name = models.CharField(max_length=60)
	units = models.CharField(max_length=60, blank=True)
	is_numeric = models.BooleanField()
	
	def __unicode__(self):
		return self.name		
	
class DatasetParameter(models.Model):
	dataset = models.ForeignKey(Dataset)
	name = models.ForeignKey(ParameterName)
	string_value = models.TextField(null=True, blank=True)
	numerical_value = models.FloatField(null=True, blank=True)

	def __unicode__(self):
		return self.name.name	
		
class DatafileParameter(models.Model):
	dataset_file = models.ForeignKey(Dataset_File)
	name = models.ForeignKey(ParameterName)
	string_value = models.TextField(null=True, blank=True)
	numerical_value = models.FloatField(null=True, blank=True)

	def __unicode__(self):
		return self.name.name		
		
class XML_data(models.Model):
	datafile = models.OneToOneField(Dataset_File, null=True, blank=True)
	dataset = models.OneToOneField(Dataset, null=True, blank=True)
	experiment = models.OneToOneField(Experiment, null=True, blank=True)
	xmlns = models.URLField(max_length=400)
	data = models.TextField()

	def __unicode__(self):
		return self.xmlns	