# pylint: disable=C0302
import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils import timezone

import dateutil.parser

from tardis.tardis_portal.auth import decorators as authz
from tardis.tardis_portal.shortcuts import return_response_error
from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.models import Experiment, Dataset, ObjectACL, \
    Schema, ParameterName, ExperimentParameterSet, ExperimentParameter, \
    ExperimentAuthor, License, Token
from tardis.tardis_portal.auth.localdb_auth import django_user, django_group

from .doi import DOI
from .models import Publication
from .utils import send_mail_to_authors
from .email_text import email_pub_released, email_pub_rejected, email_pub_reverted_to_draft
from . import tasks
from . import default_settings

logger = logging.getLogger(__name__)


@login_required
def form_view(request):
    if request.method == 'GET':
        context = {'introduction': getattr(
            settings, 'PUBLICATION_INTRODUCTION',
            "<p><strong>... introduction and publication agreement "
            "...</strong></p>")}
        return render_response_index(
            request, 'form.html', context=context)
    return process_form(request)


def validation_error(error=None):
    if error is None:
        error = 'Invalid form data was submitted ' \
                '(server-side validation failed)'
    return HttpResponse(
        json.dumps({
            'error': error}),
        content_type="application/json")


@login_required
@never_cache
def process_form(request):
    # Decode the form data
    form_state = json.loads(request.body)

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
        response = update_dataset_selection(request, form_state, publication)
        if response:
            return response
    elif form_state['action'] == 'update-extra-info':
        update_extra_info(request, form_state, publication)
    elif form_state['action'] == 'submit':
        response = submit_form(request, form_state, publication)
        if response:
            return response

    # Clear the form action and save the state
    form_state['action'] = ''
    form_state_parameter.string_value = json.dumps(form_state)
    form_state_parameter.save()

    # Set the authors even if the form hasn't been submitted yet,
    # because we want to be able to mint DOIs for draft publications
    # so they need to have at least one author:
    set_publication_authors(form_state['authors'], publication)

    return HttpResponse(json.dumps(form_state), content_type="application/json")


def update_dataset_selection(request, form_state, publication):
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
    for current_dataset in Dataset.objects.filter(experiments=publication):  # pylint: disable=not-an-iterable
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

    # No need to return an HttpResponse yet, continue processing form:
    return None


def update_extra_info(request, form_state, publication):
    # Loop through form data and create associates parameter sets
    # Any unrecognised fields or schemas are ignored!
    map_form_to_schemas(form_state['extraInfo'], publication)

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

    # No need to return an HttpResponse yet, continue processing form:
    return None


def submit_form(request, form_state, publication):
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
    pub_details_parameter_set = ExperimentParameterSet.objects.get_or_create(
        schema=pub_details_schema, experiment=publication)[0]

    # Add the acknowledgements
    acknowledgements_parameter_name = ParameterName.objects.get(
        schema=pub_details_schema,
        name='acknowledgements')
    try:
        acknowledgements_param = ExperimentParameter.objects.get(
            name=acknowledgements_parameter_name,
            parameterset=pub_details_parameter_set)
        acknowledgements_param.string_value = form_state['acknowledgements']
        acknowledgements_param.save()
    except ExperimentParameter.DoesNotExist:
        ExperimentParameter.objects.create(
            name=acknowledgements_parameter_name,
            parameterset=pub_details_parameter_set,
            string_value=form_state['acknowledgements'])

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

    # Remove the draft status
    remove_draft_status(publication)

    finalize_publication(request, publication, message=None,
                         send_email=False)
    # finalize_publication will delete the form state, so don't
    # bother saving it and return.
    form_state['action'] = ''
    return HttpResponse(json.dumps(form_state),
                        content_type="application/json")


def map_form_to_schemas(extraInfo, publication):
    for form_id, form in extraInfo.iteritems():
        try:  # Ignore form if no schema exists with this name
            schema = Schema.objects.get(namespace=form['schema'])
        except Schema.DoesNotExist:
            continue
        parameter_set = ExperimentParameterSet.objects.get_or_create(
            schema=schema, experiment=publication)[0]
        for key, value in form.iteritems():
            if key != 'schema':
                try:  # Ignore field if parameter name (key) doesn't match
                    parameter_name = ParameterName.objects.get(
                        schema=schema, name=key)
                    try:
                        parameter = ExperimentParameter.objects.get(
                            name=parameter_name, parameterset=parameter_set)
                    except ExperimentParameter.DoesNotExist:
                        parameter = ExperimentParameter.objects.create(
                            name=parameter_name, parameterset=parameter_set)
                    if parameter_name.isNumeric():
                        parameter.numerical_value = float(value)
                        parameter.save()
                    elif parameter_name.isLongString() or \
                            parameter_name.isString() or \
                            parameter_name.isURL() or \
                            parameter_name.isLink() or \
                            parameter_name.isFilename():
                        parameter.string_value = str(value)
                        parameter.save()
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


def select_forms(datasets):
    """
    This method was designed to return form templates for the publication
    form's Extra Information section, depending on a PUBLICATION_FORM_MAPPINGS
    setting which supported custom mappings between form templates, dataset
    schemas and publication schemas.

    These custom mappings have been removed for now, leaving only the generic
    Extra Information form (a textarea for each dataset).  This is because
    the way the Extra Information was updated each time the form was processed
    required deleting all of the publication draft's meatadata (except for the
    form_state) and repopulating it.  This clashes with the My Publications
    workflow's desire to add metadata (like a DOI) outside of the form.
    """
    default_form_schema = getattr(
        settings, 'GENERIC_PUBLICATION_DATASET_SCHEMA',
        default_settings.GENERIC_PUBLICATION_DATASET_SCHEMA)
    default_form = {'name': default_form_schema,
                    'template': '/static/publication-form/default-form.html',
                    'datasets': []}

    forms = []
    for dataset in datasets:
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
                          settings, 'PUBLICATION_ADMIN_GROUP',
                          default_settings.PUBLICATION_ADMIN_GROUP))[0].id),
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
                        content_type="application/json")


def require_publication_admin(f):
    def wrap(request, *args, **kwargs):
        if not request.user.groups.filter(
                name=getattr(
                    settings, 'PUBLICATION_ADMIN_GROUP',
                    default_settings.PUBLICATION_ADMIN_GROUP)).exists():
            return return_response_error(request)
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__

    return wrap


@transaction.atomic
def finalize_publication(request, publication, message=None, send_email=True):
    if publication.is_publication() and not publication.is_publication_draft() \
            and publication.public_access == Experiment.PUBLIC_ACCESS_NONE:
        # Change the access level
        if timezone.now() >= tasks.get_release_date(publication):
            publication.public_access = Experiment.PUBLIC_ACCESS_FULL
        else:
            publication.public_access = Experiment.PUBLIC_ACCESS_EMBARGO
        # Delete the form state (and containing parameter set)
        try:
            ExperimentParameterSet.objects.get(
                experimentparameter__name__name='form_state',
                experiment=publication).delete()
        except ExperimentParameterSet.DoesNotExist:
            pass
        publication.save()

        response = mint_doi_and_deactivate(request, publication.id)
        if response.status_code == 200:
            response_dict = json.loads(response.content)

            if send_email:
                subject, email_message = email_pub_released(
                    publication.title, response_dict['url'], response_dict['doi'],
                    message)
                send_mail_to_authors(publication, subject, email_message)

        # Trigger publication update
        tasks.update_publication_records.delay()

        return True

    return False


@login_required
def mint_doi_and_deactivate(request, experiment_id):
    doi = None
    url = request.build_absolute_uri(
        reverse('tardis_portal.view_experiment',
                args=(experiment_id,)))
    if getattr(settings, 'MODC_DOI_ENABLED',
               default_settings.MODC_DOI_ENABLED):
        try:
            pub_details_schema_namespace = getattr(
                settings, 'PUBLICATION_DETAILS_SCHEMA',
                default_settings.PUBLICATION_DETAILS_SCHEMA)
            pub_details_schema = Schema.objects.get(
                namespace=pub_details_schema_namespace)

            doi_parameter_name = ParameterName.objects.get(
                schema=pub_details_schema,
                name='doi')
            pub_details_parameter_set = \
                ExperimentParameterSet.objects.get_or_create(
                    schema=pub_details_schema,
                    experiment=Experiment.objects.get(id=experiment_id))[0]

            doi = DOI()
            ExperimentParameter(name=doi_parameter_name,
                                parameterset=pub_details_parameter_set,
                                string_value=doi.mint(
                                    experiment_id,
                                    reverse(
                                        'tardis_portal.view_experiment',
                                        args=(experiment_id,)))
                                ).save()
            logger.info(
                "DOI %s minted for publication ID %s" %
                (doi.doi, experiment_id))
            doi.deactivate()
            logger.info(
                "DOI %s deactivated, pending publication release criteria" %
                doi.doi)
            return HttpResponse(json.dumps(dict(doi=doi.doi, url=url)),
                                content_type='application/json')
        except ObjectDoesNotExist as err:
            if isinstance(err, ParameterName.DoesNotExist):
                logger.error(
                    "Could not find the DOI parameter name "
                    "(check schema definitions)")
                raise
            elif isinstance(err, ExperimentParameterSet.DoesNotExist):
                logger.error(
                    "Could not find the publication details parameter set")
                raise
            else:
                raise
    else:
        msg = "Can't mint DOI, because MODC_DOI_ENABLED is False."
        logger.error(msg)
        return HttpResponse(msg, status=500)


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


@login_required
def my_publications(request):
    '''
    Show drafts of public data collections, scheduled publications
    and published data.
    '''
    return render_response_index(request, 'my_publications.html')


@never_cache
@login_required
def retrieve_draft_pubs_list(request):
    '''
    json list of draft pubs accessible by the current user
    '''
    draft_pubs_data = []
    draft_publications = Publication.safe.draft_publications(request.user)\
        .order_by('-update_time')
    pub_root_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_SCHEMA_ROOT',
                          default_settings.PUBLICATION_SCHEMA_ROOT))
    form_state_pname = \
        ParameterName.objects.get(name='form_state', schema=pub_root_schema)
    pub_details_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_DETAILS_SCHEMA',
                          default_settings.PUBLICATION_DETAILS_SCHEMA))
    doi_pname = ParameterName.objects.get(name='doi', schema=pub_details_schema)
    for draft_pub in draft_publications:
        try:
            form_state_param = ExperimentParameter.objects.get(
                parameterset__experiment=draft_pub, name=form_state_pname)
            form_state = json.loads(form_state_param.string_value)
            release_date = \
                dateutil.parser.parse(form_state['embargo']).strftime("%Y-%m-%d")
        except (ObjectDoesNotExist, KeyError):
            release_date = None
        doi_param = ExperimentParameter.objects.filter(
                parameterset__experiment=draft_pub, name=doi_pname).first()
        doi = doi_param.string_value if doi_param else None
        draft_pubs_data.append(
            {
                'id': draft_pub.id,
                'title': draft_pub.title,
                'release_date': release_date,
                'doi': doi
            })

    return HttpResponse(json.dumps(draft_pubs_data),
                        content_type='application/json')


@never_cache
@login_required
def retrieve_scheduled_pubs_list(request):
    '''
    json list of scheduled pubs accessible by the current user
    '''
    scheduled_pubs_data = []
    scheduled_publications = Publication.safe.scheduled_publications(request.user)\
        .order_by('-update_time')
    pub_details_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_DETAILS_SCHEMA',
                          default_settings.PUBLICATION_DETAILS_SCHEMA))
    doi_pname = ParameterName.objects.get(name='doi', schema=pub_details_schema)
    for scheduled_pub in scheduled_publications:
        doi_param = ExperimentParameter.objects.filter(
                parameterset__experiment=scheduled_pub, name=doi_pname).first()
        doi = doi_param.string_value if doi_param else None
        scheduled_pubs_data.append(
            {
                'id': scheduled_pub.id,
                'title': scheduled_pub.title,
                'doi': doi,
                'release_date': tasks.get_release_date(scheduled_pub).strftime('%Y-%m-%d')
            })

    return HttpResponse(json.dumps(scheduled_pubs_data),
                        content_type='application/json')


@never_cache
@login_required
def retrieve_released_pubs_list(request):
    '''
    json list of released pubs accessible by the current user
    '''
    released_pubs_data = []
    released_publications = Publication.safe.released_publications(request.user)\
        .order_by('-update_time')
    pub_details_schema = Schema.objects.get(
        namespace=getattr(settings, 'PUBLICATION_DETAILS_SCHEMA',
                          default_settings.PUBLICATION_DETAILS_SCHEMA))
    doi_pname = ParameterName.objects.get(name='doi', schema=pub_details_schema)
    for released_pub in released_publications:
        doi_param = ExperimentParameter.objects.filter(
                parameterset__experiment=released_pub, name=doi_pname).first()
        doi = doi_param.string_value if doi_param else None
        released_pubs_data.append(
            {
                'id': released_pub.id,
                'title': released_pub.title,
                'doi': doi,
                'release_date': tasks.get_release_date(released_pub).strftime('%Y-%m-%d')
            })

    return HttpResponse(json.dumps(released_pubs_data),
                        content_type='application/json')


@login_required
def tokens(request, experiment_id):
    exp = Experiment.objects.get(id=experiment_id)
    context = {
        'is_owner': request.user.has_perm(
            'tardis_acls.owns_experiment', exp),
    }
    return render_response_index(
        request, 'tokens.html', context=context)


@never_cache
@login_required
def retrieve_access_list_tokens_json(request, experiment_id):
    '''
    json list of tokens associated with a given experiment
    '''
    exp = Experiment.objects.get(id=experiment_id)

    def token_url(url, token):
        return "%s?token=%s" % (url, token)

    download_urls = exp.get_download_urls()

    tokens = Token.objects.filter(experiment=experiment_id)
    token_data = []
    for token in tokens:
        token_data.append(
            {
                'expiry_date': token.expiry_date.isoformat(),
                'username': token.user.username,
                'url': request.build_absolute_uri(
                    token_url(exp.get_absolute_url(), token)),
                'download_url': request.build_absolute_uri(
                   token_url(download_urls.get('tar', None), token)),
                'id': token.id,
                'experiment_id': experiment_id,
                'is_owner': request.user.has_perm(
                    'tardis_acls.owns_experiment', token.experiment),
               })

    return HttpResponse(json.dumps(token_data),
                        content_type='application/json')


@never_cache
@login_required
def is_publication(request, experiment_id):
    '''
    Return a JSON response indicating whether the exp ID is a publication
    '''
    exp = Experiment.objects.get(id=experiment_id)
    response_data = dict(is_publication=exp.is_publication())
    return HttpResponse(json.dumps(response_data),
                        content_type='application/json')


@never_cache
@login_required
def is_publication_draft(request, experiment_id):
    '''
    Return a JSON response indicating whether the exp ID is a publication draft
    '''
    exp = Experiment.objects.get(id=experiment_id)
    response_data = dict(is_publication_draft=exp.is_publication_draft())
    return HttpResponse(json.dumps(response_data),
                        content_type='application/json')


@require_POST
def delete_publication(request, experiment_id):
    '''
    Delete the publication draft with the supplied experiment ID
    '''
    exp = Experiment.objects.get(id=experiment_id)
    if authz.has_experiment_ownership(request, exp.id):
        exp.delete()
        return HttpResponse('{"success": true}', content_type='application/json')
    return HttpResponse('{"success": false}', content_type='application/json')
