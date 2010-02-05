from django.template import Context, loader
from django.http import HttpResponse

from django.conf import settings

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.contrib.auth.decorators import login_required

from tardis.tardis_portal.ProcessExperiment import ProcessExperiment
from tardis.tardis_portal.RegisterExperimentForm import RegisterExperimentForm

from django.core.paginator import Paginator, InvalidPage, EmptyPage

from tardis.tardis_portal.models import *
from django.db.models import Sum

def render_response_index(request, *args, **kwargs):

	kwargs['context_instance'] = RequestContext(request)
	
	kwargs['context_instance']['is_authenticated'] = request.user.is_authenticated()
	kwargs['context_instance']['username'] = request.user.username
	
	#stats
	kwargs['context_instance']['public_datasets'] = Dataset.objects.filter(experiment__approved=True)
	kwargs['context_instance']['public_datafiles'] = Dataset_File.objects.filter(dataset__experiment__approved=True)
	kwargs['context_instance']['public_experiments'] = Experiment.objects.filter(approved=True)
	kwargs['context_instance']['public_pdbids'] = Pdbid.objects.filter(experiment__approved=True)

	return render_to_response(*args, **kwargs)
	
def return_response_error(request):
	c = Context({
		'status': "ERROR: Forbidden",
		'error': True		
	})

	return HttpResponseForbidden(render_response_index(request, 'tardis_portal/blank_status.html', c))
	
def return_response_not_found(request):
	c = Context({
		'status': "ERROR: Not Found",
		'error': True
	})

	return HttpResponseNotFound(render_response_index(request, 'tardis_portal/blank_status.html', c))	
	
def return_response_error_message(request, redirect_path, message):
	c = Context({
		'status': message,
		'error': True		
	})

	return HttpResponseServerError(render_response_index(request, redirect_path, c))
	
def get_accessible_experiments(user_id):
	
	# from stackoverflow question 852414
	from django.db.models import Q
	
	user = User.objects.get(pk=user_id)
	
	queries = [Q(pk=group.id) for group in user.groups.all()]

	experiments = None
	
	if queries:
		query = queries.pop()
	
		for item in queries:
			query |= item
		
		experiments = Experiment.objects.filter(query)
	
	return experiments
	
def get_owned_experiments(user_id):

	experiments = Experiment.objects.filter(experiment_owner__user__pk=user_id)

	return experiments	
	
def has_experiment_ownership(experiment_id, user_id):
	
	experiment = Experiment.objects.get(pk=experiment_id)

	eo = Experiment_Owner.objects.filter(experiment=experiment, user=user_id)

	if eo:
		return True
	else:
		return False

#custom decorator
def experiment_access_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_experiment_access(kwargs['experiment_id'], request.user.pk):
					return return_response_error(request)
				
				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

#custom decorator
def dataset_access_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_dataset_access(kwargs['dataset_id'], request.user.pk):
					return return_response_error(request)

				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

#custom decorator
def datafile_access_required(f):
        def wrap(request, *args, **kwargs):
				#if user isn't logged in it will redirect to login page
				if not request.user.is_authenticated():
					return HttpResponseRedirect("/login")
				if not has_datafile_access(kwargs['dataset_file_id'], request.user.pk):
					return return_response_error(request)

				return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

def has_experiment_access(experiment_id, user_id):

	g = Group.objects.filter(pk=experiment_id, user__pk=user_id)

	if g:
		return True
	else:
		return False
		
def has_dataset_access(dataset_id, user_id):

	experiment = Experiment.objects.get(dataset__pk=dataset_id)
	g = Group.objects.filter(pk=experiment.id, user__pk=user_id)
	

	if g:
		return True
	else:
		return False	
		
def has_datafile_access(dataset_file_id, user_id):

	experiment = Experiment.objects.get(dataset__dataset_file__pk=dataset_file_id)
	g = Group.objects.filter(pk=experiment.id, user__pk=user_id)


	if g:
		return True
	else:
		return False			

def index(request):
	
	status = ""
	
	#import feedparser

	#channels = feedparser.parse('http://tardis.edu.au/site_media/xml/localBlogCopy.xml')
	
	# 'entries': channels.entries,

	c = Context({
		'status': status,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/index.html', c))

def news(request):
	import feedparser

	channels = feedparser.parse('http://tardis.edu.au/site_media/xml/localBlogCopy.xml')
		
	c = Context({
		'entries': channels.entries,
		'subtitle': "News",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/news.html', c))			
	
def download(request, dfid):

	#todo handle missing file, general error
	if request.GET.has_key('dfid') and len(request.GET['dfid']) > 0:
		datafile = Dataset_File.objects.get(pk=request.GET['dfid'])
		if has_datafile_access(dfid, request.user.id):
			url = datafile.url
		
			if url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://'):
				return HttpResponseRedirect(datafile.url)
			else:
				file_path = settings.FILE_STORE_PATH + "/" + str(datafile.dataset.experiment.id) + "/" + datafile.url.partition('//')[2]
			
				try:
					print file_path
					f = open(file_path)
					
					response = HttpResponse(mimetype='application/octet-stream')
					response['Content-Disposition'] = 'attachment; filename=' + datafile.filename

					response.write(f.read())	
					
					return response				

				except IOError, io:
					return return_response_not_found(request)				

		else:
			return return_response_error(request)
		
def downloadTar(request):
	# Create the HttpResponse object with the appropriate headers.
	# todo handle no datafile, invalid filename, all http links (tarfile count?)
	
	if request.POST.has_key('datafile'):
		
		if not len(request.POST.getlist('datafile')) == 0:
			from django.utils.safestring import SafeUnicode
			response = HttpResponse(mimetype='application/x-tar')
			response['Content-Disposition'] = 'attachment; filename=experiment' + request.POST['expid'] + '.tar'		
		
			import StringIO

			buffer = StringIO.StringIO()	
	
			import tarfile
			import os	
			tar = tarfile.open("", "w", buffer)
	
			fileString = ""
			for dfid in request.POST.getlist('datafile'):
				datafile = Dataset_File.objects.get(pk=dfid)
				if has_datafile_access(dfid, request.user.id):
					if datafile.url.startswith('file://'):
						absolute_filename = datafile.url.partition('//')[2]
						file_string = settings.FILE_STORE_PATH + '/' + request.POST['expid'] + '/' + absolute_filename
					
						try:
							tar.add(file_string.encode('ascii'), arcname=absolute_filename.encode('ascii'), recursive=False)
						except OSError, i:
							return return_response_not_found(request)
					
			tar.close()
	
			# Get the value of the StringIO buffer and write it to the response.
			tarFile = buffer.getvalue()
			buffer.close()
			response.write(tarFile)
			return response
		else:
			return return_response_not_found(request)
	else:
		return return_response_not_found(request)
		

def about(request):
	
	c = Context({
		'subtitle': "About",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/about.html', c))	

def partners(request):

	c = Context({

	})
	return HttpResponse(render_response_index(request, 'tardis_portal/partners.html', c))	
	
def deposit(request):

	c = Context({
		'subtitle': "Deposit",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/deposit.html', c))	
	
def orca(request):
	import datetime
	
	experiments = Experiment.objects.filter(approved=True)

	c = Context({
		'experiments': experiments,
		'now': datetime.datetime.now(),
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/rif.xml', c), mimetype='application/xml')	

@experiment_access_required
def view_experiment(request, experiment_id):
	
	try:
		experiment = Experiment.objects.get(pk=experiment_id)
		author_experiments = Author_Experiment.objects.all()
		author_experiments = author_experiments.filter(experiment=experiment)
		author_experiments = author_experiments.order_by('order')
		
		datafiles = Dataset_File.objects.filter(dataset__experiment=experiment_id)

		if experiment.created_by != request.user and request.user.is_staff == False: #if exp isn't owned by current user or user isn't staff
			if experiment.approved == False: #if either unapproved or private
				return return_response_error(request)
		
		c = Context({
			'experiment': experiment,
			'authors': author_experiments,
			'datafiles': datafiles,
			# 'totalfilesize': datafiles.aggregate(Sum('size'))['size__sum'],			
			'subtitle': experiment.title,			
		})
	except Experiment.DoesNotExist, de:
		return return_response_not_found(request)
	
	return HttpResponse(render_response_index(request, 'tardis_portal/view_experiment.html', c))

def experiment_index(request):
	
	experiments = get_accessible_experiments(request.user.id)
	if experiments:
		experiments = experiments.order_by('title')
	
	c = Context({
		'experiments': experiments,
		'subtitle': "Experiment Index",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/experiment_index.html', c))

# web service, depreciated
def register_experiment_ws(request):
	# from java.lang import Exception
	import sys

	process_experiment = ProcessExperiment()
	status = ""
	if request.method == 'POST': # If the form has been submitted...

		url = request.POST['url']
		username = request.POST['username']
		password = request.POST['password']
		
		from django.contrib.auth import authenticate
		user = authenticate(username=username, password=password)
		if user is not None:
		    if not user.is_active:
		        return return_response_error(request)
		else:
		    return return_response_error(request)		

		try:
			experiments = Experiment.objects.all()
			experiments = experiments.filter(url__iexact=url)
			if not experiments:
				eid = process_experiment.register_experiment(url=url, created_by=user)
			else:
				return return_response_error_message(request, 'tardis_portal/blank_status.html', "Error: Experiment already exists")
		except IOError, i:
			return return_response_error_message(request, 'tardis_portal/blank_status.html', "Error reading file. Perhaps an incorrect URL?")				
		except:
			return return_response_error_message(request, 'tardis_portal/blank_status.html', "Unexpected Error - ", sys.exc_info()[0])				

		response = HttpResponse(status=201)
		response['Location'] = settings.TARDISURLPREFIX + "/experiment/view/" + str(eid)

		return response	
	else:
		return return_response_error(request)

# web service
def register_experiment_ws_xmldata(request):
	import sys

	process_experiment = ProcessExperiment()
	status = ""
	if request.method == 'POST': # If the form has been submitted...

		form = RegisterExperimentForm(request.POST) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass

			xmldata = form.cleaned_data['xmldata']
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			experiment_owner = form.cleaned_data['experiment_owner']

			from django.contrib.auth import authenticate
			user = authenticate(username=username, password=password)
			if user is not None:
				if not user.is_active:
					return return_response_error(request)
			else:
				return return_response_error(request)			

			eid = process_experiment.register_experiment_xmldata(xmldata=xmldata, created_by=user) # steve dummy data
			dir = settings.FILE_STORE_PATH + "/" + str(eid)
			
			#todo this entire function needs a fancy class with functions for each part..
			import os
			if not os.path.exists(dir):
			    os.makedirs(dir)
			
			file = open(dir + '/METS.xml', 'w')

			file.write(xmldata)

			file.close()	
			
			#create group
			
			#for each PI
				#check if they exist
					#if exist
						#assign to group
					#else
						#create user, generate username, randomly generated pass, send email with pass
			
			if not len(request.POST.getlist('experiment_owner')) == 0:
				for owner in request.POST.getlist('experiment_owner'):
					
					u = None
					try:
						u = User.objects.get(email__exact=owner)
					except User.DoesNotExist, ue:
						from random import choice
						import string
						
						#random password
						random_password = ""
						chars = string.letters + string.digits
						for i in range(8):
							random_password = random_password + choice(chars)					
						
						new_username = owner.partition('@')[0]
						new_username = new_username.replace(".", "_")
						
						u = User.objects.create_user(new_username, owner, random_password)
						u.save()
						
						# email new username and password
						from django.core.mail import send_mail

						recipient_list = list()

						subject = "TARDIS User Automatically Created"
						message = "A new user has been created in myTARDIS as a result of data you own being stored. Log in to " + settings.TARDISURLPREFIX + "/login with the username: " + new_username + " password: " + random_password
						from_email = "steve.androulakis@gmail.com"
						recipient_list.append(owner)
						print recipient_list
						
						send_mail(subject, message, from_email, recipient_list, fail_silently=False)						
					
					exp_owner = Experiment_Owner(experiment=Experiment.objects.get(pk=eid), user=u)
					exp_owner.save()
					g = Group(name=eid)
					g.save()
					u.groups.add(g)				

			response = HttpResponse(str(eid), status=201)
			response['Location'] = settings.TARDISURLPREFIX + "/experiment/view/" + str(eid)

			return response

	else:
		form = RegisterExperimentForm() # An unbound form

	c = Context({
		'form': form,
		'status': status,
		'subtitle': "Register Experiment",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/register_experiment.html', c))
	
@login_required()
def approve_experiment(request):
	if request.user.is_staff:
		if request.GET.has_key('id'):
			experiment_id = request.GET['id']
			
			try:
				e = Experiment.objects.get(pk=experiment_id)
				
				e.approved = True
				e.save()	

				status = "Experiment successfully approved."

				c = Context({
					'title': "Reingest Experiment",
					'status': status,
					'subtitle': "Reingest Experiment",
				})
				return HttpResponse(render_response_index(request, 'tardis_portal/blank_status.html', c))				
				
			except Experiment.DoesNotExist, de:
				return return_response_not_found(request)
		
		else:
			return return_response_not_found(request)			
	else:
		return return_response_error(request)

@datafile_access_required	
def retrieve_parameters(request, dataset_file_id):

	parameters = DatafileParameter.objects.all()
	parameters = parameters.filter(dataset_file__pk=dataset_file_id)

	c = Context({
		'parameters': parameters,
	})

	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/parameters.html', c))

@datafile_access_required
def retrieve_xml_data(request, dataset_file_id):
	from pygments import highlight
	from pygments.lexers import XmlLexer
	from pygments.formatters import HtmlFormatter
	from pygments.styles import get_style_by_name

	xml_data = XML_data.objects.get(datafile__pk=dataset_file_id)

	formatted_xml = highlight(xml_data.data, XmlLexer(), HtmlFormatter(style='default', noclasses=True))	

	c = Context({
		'formatted_xml': formatted_xml,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/xml_data.html', c))	
	
def retrieve_ftp(request, id):
	try:
		experiment = Experiment.objects.get(pk=id)

		c = Context({
			'experiment': experiment,
		})
		
	except Experiment.DoesNotExist, de:
		return return_response_not_found(request)		
		
	return HttpResponse(render_response_index(request, 'tardis_portal/site_media/applets/ftp/ftp.html', c))	

@dataset_access_required
def retrieve_datafile_list(request, dataset_id):
	from django.db.models import Count

	dataset = Dataset_File.objects.filter(dataset__pk=dataset_id).order_by('filename')

	c = Context({
		'dataset': dataset,
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/ajax/datafile_list.html', c)) 	

@login_required()
def control_panel(request):
	
	experiments = get_owned_experiments(request.user.id)
	if experiments:
		experiments = experiments.order_by('title')
	
	c = Context({
		'experiments': experiments,
		'subtitle': "Experiment Control Panel",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/control_panel.html', c))
	
def search_experiment(request):
	get = False
	experiments = Experiment.objects.all()
	experiments = Experiment.objects.order_by('title')
	
	experiments = Experiment.objects.filter(approved=True)

	if request.GET.has_key('results'):
		get = True
		if request.GET.has_key('title') and len(request.GET['title']) > 0:
			experiments = experiments.filter(title__icontains=request.GET['title'])

		if request.GET.has_key('description') and len(request.GET['description']) > 0:
			experiments = experiments.filter(description__icontains=request.GET['description'])

		if request.GET.has_key('institution_name') and len(request.GET['institution_name']) > 0:
			experiments = experiments.filter(institution_name__icontains=request.GET['institution_name'])

		if request.GET.has_key('creator') and len(request.GET['creator']) > 0:
			experiments = experiments.filter(author_experiment__author__name__icontains=request.GET['creator'])

	c = Context({
		'submitted': get,
		'experiments': experiments,
		'subtitle': "Search Experiments",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/search_experiment.html', c))	
	
def search_quick(request):
	get = False
	experiments = Experiment.objects.all()
	experiments = Experiment.objects.order_by('title')

	experiments = Experiment.objects.filter(approved=True)

	if request.GET.has_key('results'):
		get = True
		if request.GET.has_key('quicksearch') and len(request.GET['quicksearch']) > 0:
			experiments = experiments.filter(title__icontains=request.GET['quicksearch']) | \
			experiments.filter(institution_name__icontains=request.GET['quicksearch']) | \
			experiments.filter(author_experiment__author__name__icontains=request.GET['quicksearch']) | \
			experiments.filter(pdbid__pdbid__icontains=request.GET['quicksearch'])
			
			experiments = experiments.distinct()

			print experiments

	c = Context({
		'submitted': get,
		'experiments': experiments,
		'subtitle': "Search Experiments",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/search_experiment.html', c))	
	
def search_datafile(request):
	get = False
	datafile_results = Dataset_File.objects.all()
	datafile_results = Dataset_File.objects.order_by('filename')

	datafile_results = Dataset_File.objects.filter(dataset__experiment__approved=True)	

	if request.GET.has_key('results'):
		get = True
		if request.GET.has_key('filename') and len(request.GET['filename']) > 0:
			datafile_results = datafile_results.filter(filename__icontains=request.GET['filename'])

		if request.GET.has_key('diffractometerType') and request.GET['diffractometerType'] != '-':
			datafile_results = datafile_results.filter(dataset__datasetparameter__name__name__icontains='diffractometerType', \
			dataset__datasetparameter__string_value__icontains=request.GET['diffractometerType'])
			
		if request.GET.has_key('xraySource') and len(request.GET['xraySource']) > 0:
			datafile_results = datafile_results.filter(dataset__datasetparameter__name__name__icontains='xraySource', \
			dataset__datasetparameter__string_value__icontains=request.GET['xraySource'])			
		
		if request.GET.has_key('crystalName') and len(request.GET['crystalName']) > 0:
			datafile_results = datafile_results.filter(dataset__datasetparameter__name__name__icontains='crystalName', \
			dataset__datasetparameter__string_value__icontains=request.GET['crystalName'])			

		if request.GET.has_key('resLimitTo') and len(request.GET['resLimitTo']) > 0:
			datafile_results = datafile_results.filter(datafileparameter__name__name__icontains='resolutionLimit', \
			datafileparameter__numerical_value__lte=request.GET['resLimitTo'])

		if request.GET.has_key('xrayWavelengthFrom') and len(request.GET['xrayWavelengthFrom']) > 0 and request.GET.has_key('xrayWavelengthTo') and len(request.GET['xrayWavelengthTo']) > 0:
			datafile_results = datafile_results.filter(datafileparameter__name__name__icontains='xrayWavelength', \
			datafileparameter__numerical_value__range=(request.GET['xrayWavelengthFrom'], \
			request.GET['xrayWavelengthTo']))	
			
	paginator = Paginator(datafile_results, 25)	
		
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1

	# If page request (9999) is out of range, deliver last page of results.
	try:
		datafiles = paginator.page(page)
	except (EmptyPage, InvalidPage):
		datafiles = paginator.page(paginator.num_pages)
				
	c = Context({
		'submitted': get,
		'datafiles': datafiles,
		'paginator': paginator,
		'query_string': request.META['QUERY_STRING'],
		'subtitle': "Search Datafiles",
	})
	return HttpResponse(render_response_index(request, 'tardis_portal/search_datafile.html', c))