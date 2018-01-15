import json
import logging
import re

import dateutil.parser

import CifFile
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from tardis.tardis_portal.shortcuts import return_response_error
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.models import Experiment, Dataset, ObjectACL, \
    Schema, ParameterName, ExperimentParameterSet, ExperimentParameter, \
    ExperimentAuthor, License
from tardis.tardis_portal.auth.localdb_auth import django_user, django_group
from .doi import DOI
from .utils import PDBCifHelper, check_pdb_status, get_unreleased_pdb_info, \
    send_mail_to_authors, get_pub_admin_email_addresses, get_site_admin_email
from .email_text import email_pub_requires_authorisation, \
    email_pub_awaiting_approval, email_pub_approved, email_pub_rejected, \
    email_pub_reverted_to_draft
from . import tasks
from . import default_settings

logger = logging.getLogger(__name__)


@login_required
def index(request):
    if request.method == 'GET':
        context = {'introduction': getattr(
            settings, 'PUBLICATION_INTRODUCTION',
            "<p><strong>... introduction and publication agreement "
            "...</strong></p>")}
        return HttpResponse(render_response_index(
            request, 'form.html', context=context))
    return process_form(request)


@login_required
@never_cache
def process_form(request):
    # Decode the form data
    form_state = json.loads(request.body)

    def validation_error(error=None):
        if error is None:
            error = 'Invalid form data was submitted ' \
                    '(server-side validation failed)'
        return HttpResponse(
            json.dumps({
                'error': error}),
            content_type="application/json")

    # Check if the form data contains a publication ID
    # If it does, then this publication needs to be updated
    # rather than created.
    if 'publicationId' not in form_state:
        if not form_state['publicationTitle'].strip():
            return validation_error()
        publication = create_draft_publication(
            request.user, form_state['publicationTitle'],
            form_state['publicationDescription'])
        form_state['publicationId'] = publication.id
    else:
        publication = get_draft_publication(
            request.user, form_state['publicationId'])
        # Check if the publication is finalised (i.e. not in draft)
        # if it is, then refuse to process the form.
        if publication is None or not publication.is_publication_draft():
            return HttpResponseForbidden()

    # Get the form state database object
    form_state_parameter = ExperimentParameter.objects.get(
        name__name='form_state',
        name__schema__namespace=getattr(
            settings, 'PUBLICATION_SCHEMA_ROOT',
            default_settings.PUBLICATION_SCHEMA_ROOT),
        parameterset__experiment=publication)

    # Check if the form state needs to be loaded (i.e. a publication draft
    # is resumed)
    # no database changes are made if the form is resumed
    if form_state['action'] == 'resume':
        form_state = json.loads(form_state_parameter.string_value)
        return HttpResponse(json.dumps(form_state),
                            content_type="application/json")

    if form_state['action'] == 'update-dataset-selection':
        # Update the publication title/description if changed.
        # Must not be blank.
        if not form_state['publicationTitle'].strip() or \
                not form_state['publicationDescription'].strip():
            return validation_error()

        if publication.title != form_state['publicationTitle']:
            publication.title = form_state['publicationTitle']
            publication.save()
        if publication.description != form_state['publicationDescription']:
            publication.description = form_state['publicationDescription']
            publication.save()

        # Update associated datasets
        # (note: might not be efficient re: db queries)
        # ... first clear all current associations
        current_datasets = Dataset.objects.filter(experiments=publication)
        for current_dataset in current_datasets:
            current_dataset.experiments.remove(publication)
        # ... now (re)add all datasets
        selected_datasets = [ds['dataset']['id']
                             for ds in form_state['addedDatasets']]
        datasets = Dataset.objects.filter(
            experiments__in=Experiment.safe.owned_and_shared(request.user),
            pk__in=selected_datasets).distinct()

        for dataset in datasets:
            dataset.experiments.add(publication)

        # --- Get data for the next page --- #
        # Construct the disclipline-specific form based on the
        # selected datasets
        selected_forms = select_forms(datasets)
        if 'disciplineSpecificFormTemplates' in form_state:
            # clear extraInfo if the selected forms differ
            # (i.e. datasets have changed)
            if json.dumps(selected_forms) != json.dumps(
                    form_state['disciplineSpecificFormTemplates']):
                form_state['extraInfo'] = {}
        form_state['disciplineSpecificFormTemplates'] = selected_forms

    elif form_state['action'] == 'update-extra-info':
        # Clear any current parameter sets except for those belonging
        # to the publication draft schema or containing the form_state
        # parameter
        clear_publication_metadata(publication)

        # Loop through form data and create associates parameter sets
        # Any unrecognised fields or schemas are ignored!
        map_form_to_schemas(form_state['extraInfo'], publication)

        # *** Synchrotron specific ***
        # Search for beamline/EPN information associated with each dataset
        # and add to the publication.
        synchrotron_search_epn(publication)

        # --- Get data for the next page --- #
        licenses_json = get_licenses()
        form_state['licenses'] = licenses_json

        # Select the first license as default
        if licenses_json:
            if 'selectedLicenseId' not in form_state:
                form_state['selectedLicenseId'] = licenses_json[0]['id']
        else:  # No licenses configured...
            form_state['selectedLicenseId'] = -1

        # Set a default author (current user) if no previously saved data
        # By default, the form sends a list of authors of one element
        # with blank fields
        if len(form_state['authors']) == 1 and \
                not form_state['authors'][0]['name']:
            form_state['authors'] = [
                {'name': ' '.join([request.user.first_name,
                                   request.user.last_name]),
                 'institution': getattr(settings, 'DEFAULT_INSTITUTION', ''),
                 'email': request.user.email}]

    elif form_state['action'] == 'submit':
        # any final form validation should occur here
        # and specific error messages can be returned
        # to the browser before the publication's draft
        # status is removed.

        if 'acknowledge' not in form_state or not form_state['acknowledge']:
            return validation_error('You must confirm that you are '
                                    'authorised to submit this publication')

        set_publication_authors(form_state['authors'], publication)

        institutions = '; '.join(
            set([author['institution'] for author in form_state['authors']]))
        publication.institution_name = institutions

        # Attach the publication details schema
        pub_details_schema = Schema.objects.get(
            namespace=getattr(settings, 'PUBLICATION_DETAILS_SCHEMA',
                              default_settings.PUBLICATION_DETAILS_SCHEMA))
        pub_details_parameter_set = ExperimentParameterSet(
            schema=pub_details_schema,
            experiment=publication)
        pub_details_parameter_set.save()

        # Add the acknowledgements
        acknowledgements_parameter_name = ParameterName.objects.get(
            schema=pub_details_schema,
            name='acknowledgements')
        ExperimentParameter(name=acknowledgements_parameter_name,
                            parameterset=pub_details_parameter_set,
                            string_value=form_state['acknowledgements']).save()

        # Set the release date
        set_embargo_release_date(
            publication,
            dateutil.parser.parse(
                form_state[
                    'embargo']))

        # Set the license
        try:
            publication.license = License.objects.get(
                pk=form_state['selectedLicenseId'],
                is_active=True,
                allows_distribution=True)
        except License.DoesNotExist:
            publication.license = License.get_none_option_license()

        publication.save()

        # Send emails about publication in draft
        subject, message_content = email_pub_requires_authorisation(
            request.user.username,
            request.build_absolute_uri(
                reverse('tardis_portal.view_experiment',
                        args=(publication.id,))),
            request.build_absolute_uri(
                '/apps/publication-workflow/approvals/'))

        try:
            send_mail(subject,
                      message_content,
                      getattr(
                          settings, 'PUBLICATION_NOTIFICATION_SENDER_EMAIL',
                          default_settings.PUBLICATION_NOTIFICATION_SENDER_EMAIL),
                      get_pub_admin_email_addresses(),
                      fail_silently=False)

            subject, message_content = email_pub_awaiting_approval(
                publication.title)
            send_mail_to_authors(publication, subject, message_content,
                                 fail_silently=False)
        except Exception as e:
            logger.error(
                "failed to send publication notification email(s): %s" %
                repr(e)
            )
            return HttpResponse(
                json.dumps({
                    'error': 'Failed to send notification email - please '
                             'contact the %s administrator (%s), '
                             'or try again later. Your draft is saved.'
                             % (get_site_admin_email(),
                                getattr(settings, 'SITE_TITLE', 'MyTardis'))
                }),
                content_type="application/json")

        # Remove the draft status
        remove_draft_status(publication)

        # Automatically approve publications if approval is not required
        if not getattr(settings, 'PUBLICATIONS_REQUIRE_APPROVAL',
                       default_settings.PUBLICATIONS_REQUIRE_APPROVAL):
            approve_publication(request, publication, message=None,
                                send_email=False)
            # approve_publication will delete the form state, so don't
            # bother saving is and return.
            form_state['action'] = ''
            return HttpResponse(json.dumps(form_state),
                                content_type="appication/json")

        # Trigger publication record update
        tasks.update_publication_records.delay()

    # Clear the form action and save the state
    form_state['action'] = ''
    form_state_parameter.string_value = json.dumps(form_state)
    form_state_parameter.save()

    return HttpResponse(json.dumps(form_state), content_type="appication/json")


def clear_publication_metadata(publication):
    schema_root = getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                          default_settings.PUBLICATION_SCHEMA_ROOT)
    schema_draft = getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                           default_settings.PUBLICATION_DRAFT_SCHEMA)
    for parameter_set in publication.getParameterSets():
        if parameter_set.schema.namespace != schema_draft and \
                        parameter_set.schema.namespace != schema_root:
            parameter_set.delete()
        elif parameter_set.schema.namespace == schema_root:
            try:
                ExperimentParameter.objects.get(
                    name__name='form_state',
                    name__schema__namespace=schema_root,
                    parameterset=parameter_set)
            except ExperimentParameter.DoesNotExist:
                parameter_set.delete()


def map_form_to_schemas(extraInfo, publication):
    for form_id, form in extraInfo.iteritems():
        try:  # Ignore form if no schema exists with this name
            schema = Schema.objects.get(namespace=form['schema'])
        except Schema.DoesNotExist:
            continue
        parameter_set = ExperimentParameterSet(
            schema=schema, experiment=publication)
        parameter_set.save()
        for key, value in form.iteritems():
            if key != 'schema':
                try:  # Ignore field if parameter name (key) doesn't match
                    parameter_name = ParameterName.objects.get(
                        schema=schema, name=key)
                    if parameter_name.isNumeric():
                        parameter = ExperimentParameter(
                            name=parameter_name,
                            parameterset=parameter_set,
                            numerical_value=float(value))
                    elif parameter_name.isLongString() or \
                            parameter_name.isString() or \
                            parameter_name.isURL() or \
                            parameter_name.isLink() or \
                            parameter_name.isFilename():
                        parameter = ExperimentParameter(
                            name=parameter_name,
                            parameterset=parameter_set,
                            string_value=str(value))
                    else:
                        # Shouldn't happen, but here in case the parameter type
                        # is non-standard
                        continue
                    parameter.save()
                except ParameterName.DoesNotExist:
                    pass


def get_licenses():
    licenses = License.objects.filter(
        is_active=True, allows_distribution=True)
    licenses_json = []
    for license in licenses:
        l = {}
        l['id'] = license.id
        l['name'] = license.name
        l['url'] = license.url
        l['description'] = license.internal_description
        l['image'] = license.image_url
        licenses_json.append(l)
    return licenses_json


def remove_draft_status(publication):
    ExperimentParameterSet.objects.get(
        schema__namespace=getattr(
            settings, 'PUBLICATION_DRAFT_SCHEMA',
            default_settings.PUBLICATION_DRAFT_SCHEMA),
        experiment=publication).delete()


def set_publication_authors(author_list, publication):
    # Clear all current authors
    ExperimentAuthor.objects.filter(experiment=publication).delete()
    # Construct list of authors
    authorOrder = 1
    for author in author_list:
        ExperimentAuthor(experiment=publication,
                         author=author['name'],
                         institution=author['institution'],
                         email=author['email'],
                         url='',
                         order=authorOrder).save()
        authorOrder += 1


def set_embargo_release_date(publication, release_date):
    pub_schema_root = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                          default_settings.PUBLICATION_SCHEMA_ROOT))
    pub_schema_root_parameter_set = ExperimentParameterSet(
        schema=pub_schema_root,
        experiment=publication)
    pub_schema_root_parameter_set.save()
    embargo_parameter_name = ParameterName.objects.get(
        schema=pub_schema_root,
        name='embargo')
    ExperimentParameter(name=embargo_parameter_name,
                        parameterset=pub_schema_root_parameter_set,
                        datetime_value=release_date).save()


def synchrotron_search_epn(publication):
    # *** Synchrotron specific ***
    # Search for beamline/EPN information associated with each dataset
    # and add to the publication.
    try:
        synch_epn_schema = Schema.objects.get(
            namespace='http://www.tardis.edu.au/schemas/as/'
                      'experiment/2010/09/21')
        datasets = Dataset.objects.filter(experiments=publication)
        synch_experiments = Experiment.objects.filter(
            datasets__in=datasets,
            experimentparameterset__schema=synch_epn_schema).exclude(
            pk=publication.pk).distinct()
        for exp in [s for s in
                    synch_experiments if not s.is_publication()]:
            epn = ExperimentParameter.objects.get(
                name__name='EPN',
                name__schema=synch_epn_schema,
                parameterset__experiment=exp).string_value
            beamline = ExperimentParameter.objects.get(
                name__name='beamline',
                name__schema=synch_epn_schema,
                parameterset__experiment=exp).string_value

            epn_parameter_set = ExperimentParameterSet(
                schema=synch_epn_schema,
                experiment=publication)
            epn_parameter_set.save()
            epn_copy = ExperimentParameter(
                name=ParameterName.objects.get(
                    name='EPN', schema=synch_epn_schema),
                parameterset=epn_parameter_set)
            epn_copy.string_value = epn
            epn_copy.save()
            beamline_copy = ExperimentParameter(
                name=ParameterName.objects.get(
                    name='beamline', schema=synch_epn_schema),
                parameterset=epn_parameter_set)
            beamline_copy.string_value = beamline
            beamline_copy.save()
    except Schema.DoesNotExist:
        pass


def select_forms(datasets):
    default_form_schema = getattr(
        settings, 'GENERIC_PUBLICATION_DATASET_SCHEMA',
        default_settings.GENERIC_PUBLICATION_DATASET_SCHEMA)
    default_form = {'name': default_form_schema,
                    'template': '/static/publication-form/default-form.html',
                    'datasets': []}

    FORM_MAPPINGS = getattr(settings, 'PUBLICATION_FORM_MAPPINGS',
                            default_settings.PUBLICATION_FORM_MAPPINGS)
    forms = []
    for dataset in datasets:
        parametersets = dataset.getParameterSets()
        form_count = 0
        for parameterset in parametersets:
            schema_namespace = parameterset.schema.namespace
            for mapping in FORM_MAPPINGS:
                if re.match(mapping['dataset_schema'], schema_namespace):
                    form_count += 1
                    # The data returned from selected_forms() includes a list
                    # of datasets that satisfy the criteria for selecting this
                    # form.
                    # This allows the frontend to request dataset-specific
                    # information as well as general information.
                    if not any(f['name'] == mapping['publication_schema']
                               for f in forms):
                        forms.append({'name': mapping['publication_schema'],
                                      'template': mapping['form_template'],
                                      'datasets': [{
                                          'id': dataset.id,
                                          'description': dataset.description
                                      }]})
                    else:
                        idx = next(index for (index, f) in enumerate(forms)
                                   if f['name'] ==
                                   mapping['publication_schema'])
                        forms[idx]['datasets'].append({
                            'id': dataset.id,
                            'description': dataset.description})
        if not form_count:
            default_form['datasets'].append({
                'id': dataset.id,
                'description': dataset.description
            })

    if default_form['datasets']:
        forms.append(default_form)

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
              entityId=str(
                  Group.objects.get_or_create(
                      name=getattr(
                          settings, 'PUBLICATION_OWNER_GROUP',
                          default_settings.PUBLICATION_OWNER_GROUP))[0].id),
              canRead=True,
              canWrite=True,
              canDelete=True,
              isOwner=True,
              aclOwnershipType=ObjectACL.OWNER_OWNED).save()

    publication_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                          default_settings.PUBLICATION_SCHEMA_ROOT))

    # Attach draft schema
    draft_publication_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                          default_settings.PUBLICATION_DRAFT_SCHEMA))
    ExperimentParameterSet(schema=draft_publication_schema,
                           experiment=experiment).save()

    # Attach root schema and blank form_state parameter
    publication_root_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                          default_settings.PUBLICATION_SCHEMA_ROOT))
    publication_root_parameter_set = ExperimentParameterSet(
        schema=publication_schema,
        experiment=experiment)
    publication_root_parameter_set.save()
    form_state_param_name = ParameterName.objects.get(
        schema=publication_root_schema, name='form_state')
    ExperimentParameter(name=form_state_param_name,
                        parameterset=publication_root_parameter_set).save()

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
    experiments = Experiment.safe.owned_and_shared(request.user) \
        .order_by('title')
    json_response = []
    for experiment in experiments:
        if not experiment.is_publication():
            experiment_json = {'id': experiment.id,
                               'title': experiment.title,
                               'institution_name': experiment.institution_name,
                               'description': experiment.description}
            datasets = Dataset.objects.filter(experiments=experiment) \
                .order_by('description')
            dataset_json = []
            for dataset in datasets:
                dataset_json.append({'id': dataset.id,
                                     'description': dataset.description,
                                     'directory': dataset.directory})
            experiment_json['datasets'] = dataset_json
            json_response.append(experiment_json)
    return HttpResponse(json.dumps(json_response),
                        content_type="appication/json")


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
    except CifFile.StarError:
        # If it's not released, check if it's a valid PDB ID
        status = check_pdb_status(pdb_id)
        if status == 'UNRELEASED':
            result = get_unreleased_pdb_info(pdb_id)
            result['status'] = 'UNRELEASED'
        else:
            result = {'title': '',
                      'authors': '',
                      'status': 'UNKNOWN'}

    return HttpResponse(json.dumps(result), content_type="application/json")


def require_publication_admin(f):
    def wrap(request, *args, **kwargs):
        if not request.user.groups.filter(
                name=getattr(
                    settings, 'PUBLICATION_OWNER_GROUP',
                    default_settings.PUBLICATION_OWNER_GROUP)).exists():
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__

    return wrap


@login_required
@require_publication_admin
def approval_view(request):
    if request.method == 'GET':
        return HttpResponse(render_response_index(
            request, 'publication_approval.html'))
    return approval_ajax(request)


def approval_ajax(request):
    # Decode the form data
    json_request = json.loads(request.body)

    # wrapper to return json
    def response(obj):
        return HttpResponse(json.dumps(obj), content_type="application/json")

    def json_get_publications_awaiting_approval():
        pubs = []
        for pub in get_publications_awaiting_approval():
            pubs.append({
                'id': pub.id,
                'title': pub.title,
                'description': pub.description,
                'authors': '; '.join([author.author for author in
                                      ExperimentAuthor.objects.filter(
                                          experiment=pub)])
            })
        return pubs

    if 'action' in json_request:
        if json_request['action'] == 'approve':
            pub_id = json_request['id']
            message = json_request['message']
            try:
                approve_publication(request, Experiment.objects.get(pk=pub_id),
                                    message)
            except Experiment.DoesNotExist:
                pass
        elif json_request['action'] == 'revert':
            pub_id = json_request['id']
            message = json_request['message']
            try:
                revert_publication_to_draft(
                    Experiment.objects.get(pk=pub_id), message)
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
    pub_schema = getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                         default_settings.PUBLICATION_SCHEMA_ROOT)
    pub_schema_draft = getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                               default_settings.PUBLICATION_DRAFT_SCHEMA)
    pubs = Experiment.objects.filter(
        public_access=Experiment.PUBLIC_ACCESS_NONE,
        experimentparameterset__schema__namespace=pub_schema).exclude(
        experimentparameterset__schema__namespace=pub_schema_draft
    ).distinct()
    return pubs


@transaction.atomic
def approve_publication(request, publication, message=None, send_email=True):
    if publication.is_publication() and not publication.is_publication_draft() \
            and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:
        # Change the access level
        publication.public_access = Experiment.PUBLIC_ACCESS_EMBARGO

        # Delete the form state (and containing parameter set)
        try:
            ExperimentParameterSet.objects.get(
                experimentparameter__name__name='form_state',
                experiment=publication).delete()
        except ExperimentParameterSet.DoesNotExist:
            pass
        publication.save()

        # Set the publication owner appropriately
        # (sets the managedBy relatedObject in rif-cs)
        pub_data_admin_username = getattr(
            settings, 'PUBLICATION_DATA_ADMIN',
            default_settings.PUBLICATION_DATA_ADMIN)
        if pub_data_admin_username is not None:
            try:
                pub_data_admin = User.objects.get(
                    username=pub_data_admin_username)
                # Remove ownership status for all current owners
                current_owners = ObjectACL.objects.filter(
                    pluginId='django_user',
                    content_type=publication.get_ct(),
                    object_id=publication.id,
                    isOwner=True)
                for owner in current_owners:
                    owner.isOwner = False
                    owner.save()

                # Add the data administrator as an owner
                data_admin_acl, _ = ObjectACL.objects.get_or_create(
                    content_type=publication.get_ct(),
                    object_id=publication.id,
                    pluginId=django_user,
                    entityId=str(pub_data_admin.id),
                    aclOwnershipType=ObjectACL.OWNER_OWNED)
                data_admin_acl.canRead = True
                data_admin_acl.canWrite = True
                data_admin_acl.canDelete = True
                data_admin_acl.isOwner = True
                data_admin_acl.save()
            except User.DoesNotExist:
                logger.error("Could not change publication owner to "
                             "PUBLICATION_DATA_ADMIN; no such user.")

        doi = None
        url = request.build_absolute_uri(
            reverse('tardis_portal.view_experiment',
                    args=(publication.id,)))
        if getattr(settings, 'MODC_DOI_ENABLED',
                   default_settings.MODC_DOI_ENABLED):
            try:
                pub_details_schema = getattr(
                    settings, 'PUBLICATION_DETAILS_SCHEMA',
                    default_settings.PUBLICATION_DETAILS_SCHEMA)

                doi_parameter_name = ParameterName.objects.get(
                    schema__namespace=pub_details_schema,
                    name='doi')
                pub_details_parameter_set = ExperimentParameterSet.objects.get(
                    schema__namespace=pub_details_schema,
                    experiment=publication)

                doi = DOI()
                ExperimentParameter(name=doi_parameter_name,
                                    parameterset=pub_details_parameter_set,
                                    string_value=doi.mint(
                                        publication.id,
                                        reverse(
                                            'tardis_portal.view_experiment',
                                            args=(publication.id,)))
                                    ).save()
                logger.info(
                    "DOI %s minted for publication ID %i" %
                    (doi.doi, publication.id))
                doi.deactivate()
                logger.info(
                    "DOI %s deactivated, pending publication release criteria" %
                    doi.doi)
            except ParameterName.DoesNotExist:
                logger.error(
                    "Could not find the DOI parameter name (check schema definitions)")
            except ExperimentParameterSet.DoesNotExist:
                logger.error(
                    "Could not find the publication details parameter set")

        if send_email:
            subject, email_message = email_pub_approved(
                publication.title, url, doi, message)
            send_mail_to_authors(publication, subject, email_message)

        # Trigger publication update
        tasks.update_publication_records.delay()

        return True

    return False


def reject_publication(publication, message=None):
    if publication.is_publication() and not publication.is_publication_draft() \
            and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:
        subject, email_message = email_pub_rejected(publication.title, message)

        send_mail_to_authors(publication, subject, email_message)

        publication.delete()

        return True
    return False


def revert_publication_to_draft(publication, message=None):
    # Anything with the form_state parameter can be reverted to draft
    try:
        # Check that the publication is currently finalised but not released
        if publication.is_publication_draft() and publication.is_publication() \
                and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:
            return False

        # Check that form_state exists (raises an exception if not)
        schema_ns_root = getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                                 default_settings.PUBLICATION_SCHEMA_ROOT)
        ExperimentParameter.objects.get(
            name__name='form_state',
            name__schema__namespace=schema_ns_root,
            parameterset__experiment=publication)

        # Reduce access level to none
        publication.public_access = Experiment.PUBLIC_ACCESS_NONE
        publication.save()

        # Add the draft schema
        draft_schema_ns = getattr(settings, 'PUBLICATION_DRAFT_SCHEMA',
                                  default_settings.PUBLICATION_DRAFT_SCHEMA)
        draft_publication_schema = Schema.objects.get(
            namespace=draft_schema_ns)
        ExperimentParameterSet(schema=draft_publication_schema,
                               experiment=publication).save()

        # Delete all metadata except for the form_state
        # Clear any current parameter sets except for those belonging
        # to the publication draft schema or containing the form_state
        # parameter
        for parameter_set in publication.getParameterSets():
            if parameter_set.schema.namespace != draft_schema_ns and \
                            parameter_set.schema.namespace != schema_ns_root:
                parameter_set.delete()
            elif parameter_set.schema.namespace == schema_ns_root:
                try:
                    ExperimentParameter.objects.get(
                        name__name='form_state',
                        name__schema__namespace=schema_ns_root,
                        parameterset=parameter_set)
                except ExperimentParameter.DoesNotExist:
                    parameter_set.delete()

        # Send notification emails -- must be done before authors are deleted
        subject, email_message = email_pub_reverted_to_draft(
            publication.title, message)

        send_mail_to_authors(publication, subject, email_message)

        # Delete all author records
        ExperimentAuthor.objects.filter(experiment=publication).delete()

        return True

    except ExperimentParameter.DoesNotExist:
        return False
