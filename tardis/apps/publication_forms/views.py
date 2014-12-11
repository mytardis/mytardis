import json
import re

import dateutil.parser
import StarFile

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.models import Experiment, Dataset, ObjectACL, \
    Schema, ParameterName, ExperimentParameterSet, ExperimentParameter, \
    ExperimentAuthor, License
from tardis.tardis_portal.auth.localdb_auth import django_user, django_group
from tardis.tardis_portal.auth import decorators as authz
from doi import DOI_minter
from utils import PDBCifHelper, check_pdb_status, get_unreleased_pdb_info, send_mail_to_authors


@login_required
def index(request):
    if request.method == 'GET':
        return HttpResponse(render_response_index(request, 'form.html'))
    else:
        return process_form(request)


@login_required
@never_cache
def process_form(request):
    # Decode the form data
    form_state = json.loads(request.body)

    def validation_error():
        return HttpResponse(json.dumps({'error': 'Invalid form data was submitted (server-side validation failed)'}),
                            mimetype="application/json")

    # Check if the form data contains a publication ID
    # If it does, then this publication needs to be updated
    # rather than created.
    if 'publication_id' not in form_state:
        if not form_state['publicationTitle'].strip():
            return validation_error()
        publication = create_draft_publication(request.user, form_state['publicationTitle'],
                                               form_state['publicationDescription'])
        form_state['publication_id'] = publication.id
    else:
        publication = get_draft_publication(request.user, form_state['publication_id'])
        # Check if the publication is finalised (i.e. not in draft)
        # if it is, then refuse to process the form.
        if not publication.is_publication_draft():
            return HttpResponseForbidden()

    # Get the form state database object
    form_state_parameter = ExperimentParameter.objects.get(name__name='form_state',
                                                           name__schema__namespace=settings.PUBLICATION_SCHEMA_ROOT,
                                                           parameterset__experiment=publication)

    # Check if the form state needs to be loaded (i.e. a publication draft is resumed)
    # no database changes are made if the form is resumed
    if form_state['action'] == 'resume':
        form_state = json.loads(form_state_parameter.string_value)
        return HttpResponse(json.dumps(form_state), mimetype="application/json")

    if form_state['action'] == 'update-dataset-selection':
        # Update the publication title/description if changed. Must not be blank.
        if not form_state['publicationTitle'].strip() or not form_state['publicationDescription'].strip():
            return validation_error()

        if publication.title != form_state['publicationTitle']:
            publication.title = form_state['publicationTitle']
            publication.save()
        if publication.description != form_state['publicationDescription']:
            publication.description = form_state['publicationDescription']
            publication.save()

        # Update associated datasets (note: might not be efficient re: db queries)
        # ... first clear all current associations
        current_datasets = Dataset.objects.filter(experiments=publication)
        for current_dataset in current_datasets:
            current_dataset.experiments.remove(publication)
        # ... now (re)add all datasets
        selected_datasets = [ds['dataset']['id'] for ds in form_state['addedDatasets']]
        datasets = Dataset.objects.filter(experiments__in=Experiment.safe.owned(request.user),
                                          pk__in=selected_datasets).distinct()
        for dataset in datasets:
            dataset.experiments.add(publication)

        ### Get data for the next page ###
        # Construct the disclipline-specific form based on the selected datasets
        selected_forms = select_forms(datasets)
        if 'disciplineSpecificFormTemplates' in form_state:
            # clear extraInfo if the selected forms differ (i.e. datasets have changed)
            if json.dumps(selected_forms) != json.dumps(form_state['disciplineSpecificFormTemplates']):
                form_state['extraInfo'] = {};
        form_state['disciplineSpecificFormTemplates'] = selected_forms

    elif form_state['action'] == 'update-extra-info':
        # Clear any current parameter sets except for those belonging
        # to the publication draft schema or containing the form_state
        # parameter
        for parameter_set in publication.getParameterSets():
            if parameter_set.schema.namespace != settings.PUBLICATION_DRAFT_SCHEMA and \
                            parameter_set.schema.namespace != settings.PUBLICATION_SCHEMA_ROOT:
                parameter_set.delete()
            elif parameter_set.schema.namespace == settings.PUBLICATION_SCHEMA_ROOT:
                try:
                    ExperimentParameter.objects.get(name__name='form_state',
                                                    name__schema__namespace=settings.PUBLICATION_SCHEMA_ROOT,
                                                    parameterset=parameter_set)
                except ExperimentParameter.DoesNotExist:
                    parameter_set.delete()

        # Loop through form data and create associates parameter sets
        # Any unrecognised fields or schemas are ignored!
        for form_id, form in form_state['extraInfo'].iteritems():
            try:  # Ignore form if no schema exists with this name
                schema = Schema.objects.get(namespace=form['schema'])
            except Schema.DoesNotExist:
                continue
            parameter_set = ExperimentParameterSet(schema=schema, experiment=publication)
            parameter_set.save()
            for key, value in form.iteritems():
                if key != 'schema':
                    try:  # Ignore field if parameter name (key) doesn't match
                        parameter_name = ParameterName.objects.get(schema=schema, name=key)
                        if parameter_name.isNumeric():
                            parameter = ExperimentParameter(name=parameter_name,
                                                            parameterset=parameter_set,
                                                            numerical_value=float(value))
                        elif parameter_name.isLongString() or parameter_name.isString() or \
                                parameter_name.isURL() or parameter_name.isLink() or \
                                parameter_name.isFilename():
                            parameter = ExperimentParameter(name=parameter_name,
                                                            parameterset=parameter_set,
                                                            string_value=str(value))
                        parameter.save()
                    except ParameterName.DoesNotExist:
                        pass

        ### --- Get data for the next page --- ###
        licenses = License.objects.filter(is_active=True, allows_distribution=True)
        licenses_json = []
        for license in licenses:
            l = {}
            l['id'] = license.id
            l['name'] = license.name
            l['url'] = license.url
            l['description'] = license.internal_description
            l['image'] = license.image_url
            licenses_json.append(l)
        form_state['licenses'] = licenses_json

        # Select the first license as default
        if licenses_json:
            if 'selectedLicenseId' not in form_state:
                form_state['selectedLicenseId'] = licenses_json[0]['id']
        else:  # No licenses configured...
            form_state['selectedLicenseId'] = -1

        # Set a default author (current user) if no previously saved data
        # By default, the form sends a list of authors of one element with blank fields
        if len(form_state['authors']) == 1 and not form_state['authors'][0]['name']:
            form_state['authors'] = [{'name':request.user.first_name+" "+request.user.last_name,
                                      'institution':'',
                                      'email':request.user.email}]

    elif form_state['action'] == 'submit':
        # any final form validation should occur here
        # and specific error messages can be returned
        # to the browser before the publication's draft
        # status is removed.

        # Construct list of authors
        authorOrder = 1
        for author in form_state['authors']:
            ExperimentAuthor(experiment=publication,
                             author=author['name'],
                             institution=author['institution'],
                             email=author['email'],
                             order=authorOrder).save()
            authorOrder += 1

        institutions = '; '.join(set([author['institution'] for author in form_state['authors']]))
        publication.institution_name = institutions

        # Attach the publication details schema
        pub_details_schema = Schema.objects.get(namespace=settings.PUBLICATION_DETAILS_SCHEMA)
        pub_details_parameter_set = ExperimentParameterSet(schema=pub_details_schema,
                                                           experiment=publication)
        pub_details_parameter_set.save()

        # Add the acknowledgements
        acknowledgements_parameter_name = ParameterName.objects.get(schema=pub_details_schema,
                                                                    name='acknowledgements')
        ExperimentParameter(name=acknowledgements_parameter_name,
                            parameterset=pub_details_parameter_set,
                            string_value=form_state['acknowledgements']).save()

        # DOIs are generated during approval, so this is just a placeholder.
        doi = '---'
        doi_parameter_name = ParameterName.objects.get(schema=pub_details_schema,
                                                       name='doi')
        ExperimentParameter(name=doi_parameter_name,
                            parameterset=pub_details_parameter_set,
                            string_value=doi).save()

        # Set the release date
        release_date = dateutil.parser.parse(form_state['embargo'])
        pub_schema_root = Schema.objects.get(namespace=settings.PUBLICATION_SCHEMA_ROOT)
        pub_schema_root_parameter_set = ExperimentParameterSet(schema=pub_schema_root,
                                                               experiment=publication)
        pub_schema_root_parameter_set.save()
        embargo_parameter_name = ParameterName.objects.get(schema=pub_schema_root,
                                                           name='embargo')
        ExperimentParameter(name=embargo_parameter_name,
                            parameterset=pub_schema_root_parameter_set,
                            datetime_value=release_date).save()

        # Set the license
        try:
            publication.license = License.objects.get(pk=form_state['selectedLicenseId'],
                                                      is_active=True,
                                                      allows_distribution=True)
        except License.DoesNotExist:
            publication.license = License.get_none_option_license()

        publication.save()

        # Remove the draft status
        ExperimentParameterSet.objects.get(schema__namespace=settings.PUBLICATION_DRAFT_SCHEMA,
                                           experiment=publication).delete()

        # Send emails about publication in draft
        # -- Get list of emails for all publication administrators
        pub_admin_email_addresses = [user.email
                                     for user in Group.objects.get(name=settings.PUBLICATION_OWNER_GROUP).user_set.all()
                                     if user.email]
        message_content = '''Hello!
A publication has been submitted by %s and requires approval by a publication administrator.
You may view the publication here: %s

This publication will not be publicly accessible until all embargo conditions are met following approval.
To approve this publication, please access the publication approvals interface here: %s
''' % (request.user.username,
       request.build_absolute_uri('/experiment/view/' + str(publication.id) + '/'),
       request.build_absolute_uri('/apps/publication-forms/approvals/'))

        send_mail('[TARDIS] Publication requires authorisation',
                  message_content,
                  'store.star.help@monash.edu',
                  pub_admin_email_addresses,
                  fail_silently=True)

        message_content = '''Hello!
Your publication, %s, has been submitted and is awaiting approval by an administrator.
You will receive a notification once his has occurred.''' % publication.title
        send_mail_to_authors(publication, '[TARDIS] Publication submitted', message_content)

    # Clear the form action and save the state
    form_state['action'] = ''
    form_state_parameter.string_value = json.dumps(form_state)
    form_state_parameter.save()

    return HttpResponse(json.dumps(form_state), mimetype="appication/json")


def select_forms(datasets):
    default_form = [{'name': 'default', 'template': '/static/publication-form/default-form.html'}]

    if not hasattr(settings, 'PUBLICATION_FORM_MAPPINGS'):
        return default_form

    FORM_MAPPINGS = settings.PUBLICATION_FORM_MAPPINGS
    forms = []
    for dataset in datasets:
        parametersets = dataset.getParameterSets()
        for parameterset in parametersets:
            schema_namespace = parameterset.schema.namespace
            for mapping in FORM_MAPPINGS:
                if re.match(mapping['dataset_schema'], schema_namespace):
                    # The data returned from selected_forms() includes a list of datasets
                    # that satisfy the criteria for selecting this form.
                    # This allows the frontend to request dataset-specific information
                    # as well as generall information.
                    if not any(f['name'] == mapping['publication_schema'] for f in forms):
                        forms.append({'name': mapping['publication_schema'],
                                      'template': mapping['form_template'],
                                      'datasets': [{'id': dataset.id,
                                                    'description': dataset.description}]})
                    else:
                        idx = next(index for (index, f) in enumerate(forms)
                                   if f['name'] == mapping['publication_schema'])
                        forms[idx]['datasets'].append({'id': dataset.id,
                                                       'description': dataset.description})

    if not forms:
        return default_form
    else:
        return forms


def create_draft_publication(user, publication_title, publication_description):
    # Note: Maybe this logic can be taken from the tardis_portal/views.py?

    experiment = Experiment(created_by=user,
                            title=publication_title,
                            description=publication_description)
    experiment.save()

    ObjectACL(content_object=experiment,
              pluginId=django_user,
              entityId=str(user.id),
              canRead=True,
              canWrite=False,
              canDelete=False,
              isOwner=True,
              aclOwnershipType=ObjectACL.OWNER_OWNED).save()

    ObjectACL(content_object=experiment,
              pluginId=django_group,
              entityId=str(Group.objects.get(name=settings.PUBLICATION_OWNER_GROUP).id),
              canRead=True,
              canWrite=True,
              canDelete=True,
              isOwner=True,
              aclOwnershipType=ObjectACL.OWNER_OWNED).save()

    publication_schema = Schema.objects.get(
        namespace=settings.PUBLICATION_SCHEMA_ROOT)

    # Attach draft schema
    draft_publication_schema = Schema.objects.get(
        namespace=settings.PUBLICATION_DRAFT_SCHEMA)
    ExperimentParameterSet(schema=draft_publication_schema,
                           experiment=experiment).save()

    # Attach root schema and blank form_state parameter
    publication_root_schema = Schema.objects.get(
        namespace=settings.PUBLICATION_SCHEMA_ROOT)
    publication_root_parameter_set = ExperimentParameterSet(schema=publication_schema,
                                                            experiment=experiment)
    publication_root_parameter_set.save()
    form_state_param_name = ParameterName.objects.get(schema=publication_root_schema, name='form_state')
    ExperimentParameter(name=form_state_param_name, parameterset=publication_root_parameter_set).save()

    return experiment


def get_draft_publication(user, publication_id):
    for exp in Experiment.safe.owned(user):
        if exp.id == publication_id and exp.is_publication_draft():
            return exp

    for group in user.groups.all():
        for exp in Experiment.safe.owned_by_group(group):
            if exp.id == publication_id and exp.is_publication_draft():
                return exp

    return None


@login_required
@never_cache
def fetch_experiments_and_datasets(request):
    experiments = Experiment.safe.owned(request.user);
    json_response = []
    for experiment in experiments:
        if not experiment.is_publication():
            experiment_json = {'id': experiment.id,
                               'title': experiment.title,
                               'institution_name': experiment.institution_name,
                               'description': experiment.description}
            datasets = Dataset.objects.filter(experiments=experiment)
            dataset_json = []
            for dataset in datasets:
                dataset_json.append({'id': dataset.id,
                                     'description': dataset.description,
                                     'directory': dataset.directory})
            experiment_json['datasets'] = dataset_json
            json_response.append(experiment_json)
    return HttpResponse(json.dumps(json_response), mimetype="appication/json")


def pdb_helper(request, pdb_id):
    try:
        # Do this if the PDB is already released...
        pdb = PDBCifHelper(pdb_id)
        citations = pdb.get_citations()
        authors = ', '.join(citations[0]['authors'])
        title = citations[0]['title']
        result = {
            'title': title,
            'authors': authors,
            'status': 'RELEASED'
        }
    except StarFile.StarError:
        # If it's not released, check if it's a valid PDB ID
        status = check_pdb_status(pdb_id)
        if status == 'UNRELEASED':
            result = get_unreleased_pdb_info(pdb_id)
            result['status'] = 'UNRELEASED'
        else:
            result = {'title': '',
                      'authors': '',
                      'status': 'UNKNOWN'}

    return HttpResponse(json.dumps(result), mimetype="application/json")


@login_required
@authz.require_publication_admin
def approval_view(request):
    if request.method == 'GET':
        return HttpResponse(render_response_index(request, 'publication_approval.html'))
    else:
        return approval_ajax(request)


def approval_ajax(request):
    # Decode the form data
    json_request = json.loads(request.body)

    # wrapper to return json
    def response(obj):
        return HttpResponse(json.dumps(obj), mimetype="application/json")

    def json_get_publications_awaiting_approval():
        pubs = []
        for pub in get_publications_awaiting_approval():
            pubs.append({
                'id': pub.id,
                'title': pub.title,
                'description': pub.description,
                'authors': '; '.join([ author.author for author in ExperimentAuthor.objects.filter(experiment=pub)])
            })
        return pubs

    if 'action' in json_request:
        if json_request['action'] == 'approve':
            pub_id = json_request['id']
            message = json_request['message']
            try:
                approve_publication(Experiment.objects.get(pk=pub_id), message)
            except Experiment.DoesNotExist:
                pass
        elif json_request['action'] == 'revert':
            pub_id = json_request['id']
            message = json_request['message']
            try:
                revert_publication_to_draft(Experiment.objects.get(pk=pub_id), message)
            except Experiment.DoesNotExist:
                pass
        elif json_request['action'] == 'reject':
            pub_id = json_request['id']
            message = json_request['message']
            try:
                reject_publication(Experiment.objects.get(pk=pub_id), message)
            except Experiment.DoesNotExist:
                pass

    return response(json_get_publications_awaiting_approval())

def get_publications_awaiting_approval():
    PUB_SCHEMA = settings.PUBLICATION_SCHEMA_ROOT
    PUB_SCHEMA_DRAFT = settings.PUBLICATION_DRAFT_SCHEMA
    pubs = Experiment.objects.filter(public_access=Experiment.PUBLIC_ACCESS_NONE,
                                       experimentparameterset__schema__namespace=PUB_SCHEMA)\
        .exclude(experimentparameterset__schema__namespace=PUB_SCHEMA_DRAFT).distinct()
    return pubs


def approve_publication(publication, message=None):
    if publication.is_publication() and not publication.is_publication_draft()\
            and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:
        # Change the access level
        publication.public_access = Experiment.PUBLIC_ACCESS_EMBARGO

        # Delete the form state (and containing parameter set)
        try:
            ExperimentParameterSet.objects.get(experimentparameter__name__name='form_state',
                                               experiment=publication).delete()
        except ExperimentParameterSet.DoesNotExist:
            pass

        publication.save()

        doi = None
        try:
            doi_param = ExperimentParameter.objects.get(name__name='doi',
                                                        name__schema__namespace=settings.PUBLICATION_DETAILS_SCHEMA,
                                                        parameterset__experiment=publication)
            doi = DOI_minter().mint(publication.id, 'experiment/view/'+str(publication.id)+'/')
            doi_param.string_value = doi
            doi_param.save()
        except ExperimentParameter.DoesNotExist:
            pass

        email_message='''Hello!
Your publication, %s, has been approved for release and will appear online following any embargo conditions.
''' % publication.title

        if doi is not None:
            email_message += '''A DOI has been assigned to this publication (%s) and will become active once your publication is released.
You may use cite using this DOI immediately.''' % doi

        if message:
            email_message += ''' ---
%s''' % message

        send_mail_to_authors(publication, '[TARDIS] Publication approved', email_message)

        return True

    return False


def reject_publication(publication, message=None):
    if publication.is_publication() and not publication.is_publication_draft()\
            and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:

        email_message='''Hello!
Your publication, %s, is unable to be released. Please contact your system administrator for further information.
''' % publication.title

        if message:
            email_message += ''' ---
%s''' % message

        send_mail_to_authors(publication, '[TARDIS] Publication rejected', email_message)

        publication.delete()

        return True
    return False


def revert_publication_to_draft(publication, message=None):
    # Anything with the form_state parameter can be reverted to draft
    try:
        # Check that the publication is currently finalised but not released
        if publication.is_publication_draft() and publication.is_publication()\
                and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:
            return False

        # Check that form_state exists (raises an exception if not)
        ExperimentParameter.objects.get(name__name='form_state',
                                        name__schema__namespace=settings.PUBLICATION_SCHEMA_ROOT,
                                        parameterset__experiment=publication)

        # Reduce access level to none
        publication.public_access = Experiment.PUBLIC_ACCESS_NONE
        publication.save()

        # Add the draft schema
        draft_publication_schema = Schema.objects.get(
            namespace=settings.PUBLICATION_DRAFT_SCHEMA)
        ExperimentParameterSet(schema=draft_publication_schema,
                               experiment=publication).save()

        # Delete all metadata except for the form_state
        # Clear any current parameter sets except for those belonging
        # to the publication draft schema or containing the form_state
        # parameter
        for parameter_set in publication.getParameterSets():
            if parameter_set.schema.namespace != settings.PUBLICATION_DRAFT_SCHEMA and \
                            parameter_set.schema.namespace != settings.PUBLICATION_SCHEMA_ROOT:
                parameter_set.delete()
            elif parameter_set.schema.namespace == settings.PUBLICATION_SCHEMA_ROOT:
                try:
                    ExperimentParameter.objects.get(name__name='form_state',
                                                    name__schema__namespace=settings.PUBLICATION_SCHEMA_ROOT,
                                                    parameterset=parameter_set)
                except ExperimentParameter.DoesNotExist:
                    parameter_set.delete()

        # Send notification emails -- must be done before authors are deleted
        email_message='''Hello!
Your publication, %s, has been reverted to draft and may now be amended.
''' % publication.title

        if message:
            email_message += ''' ---
%s''' % message

        send_mail_to_authors(publication, '[TARDIS] Publication reverted to draft', email_message)


        # Delete all author records
        ExperimentAuthor.objects.filter(experiment=publication).delete()

        return True

    except ExperimentParameter.DoesNotExist:
        return False
