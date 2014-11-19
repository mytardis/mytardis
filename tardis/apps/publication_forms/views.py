
import json
import re

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseRedirect,\
    HttpResponseForbidden
from django.template import Context
from django.conf import settings

from tardis.tardis_portal.shortcuts import render_response_index
from tardis.tardis_portal.models import Experiment, Dataset, ObjectACL,\
    Schema, ParameterName, ExperimentParameterSet, ExperimentParameter
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.managers import ExperimentManager

@login_required
def index(request):
    if request.method == 'GET':
        return HttpResponse(render_response_index(request,'form.html'))
    else:
        return process_form(request)


@login_required
@never_cache
def process_form(request):
    # Decode the form data
    form_state = json.loads(request.body)

    def validation_error():
        return HttpResponse(json.dumps({'error':'Invalid form data was submitted (server-side validation failed)'}), mimetype="appication/json")

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
            name__schema__namespace=settings.PUBLICATION_DRAFT_SCHEMA_NAMESPACE,
            parameterset__experiment=publication)

    # Check if the form state needs to be loaded (i.e. a publication draft is resumed)
    # no database changes are made if the form is resumed
    if form_state['action'] == 'resume':
        form_state = json.loads(form_state_parameter.string_value)
        return HttpResponse(json.dumps(form_state), mimetype="application/json")

    if form_state['action'] == 'update-dataset-selection':
        # Update the publiation title/description if changed. Must not be blank.
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

        # Construct the disclipline-specific form based on the selected datasets
        selected_forms = select_forms(datasets)
        if 'disciplineSpecificFormTemplates' in form_state:
            # clear extraInfo if the selected forms differ (i.e. datasets have changed)
            if json.dumps(selected_forms) != json.dumps(form_state['disciplineSpecificFormTemplates']):
                form_state['extraInfo'] = {};
        form_state['disciplineSpecificFormTemplates'] = selected_forms

    elif form_state['action'] == 'update-extra-info':
        # Clear any current parameter sets
        for parameter_set in publication.getParameterSets():
            if parameter_set.schema.namespace != settings.PUBLICATION_DRAFT_SCHEMA_NAMESPACE:
                parameter_set.delete()

        # Loop through form data and create associates parameter sets
        # Any unrecognised fields or schemas are ignored!
        for form_id,form in form_state['extraInfo'].iteritems():
            try: # Ignore form if no schema exists with this name
                schema = Schema.objects.get(namespace=form['schema'])
            except Schema.DoesNotExist:
                continue
            parameter_set = ExperimentParameterSet(schema=schema, experiment=publication)
            parameter_set.save()
            for key,value in form.iteritems():
                if key != 'schema':
                    try: # Ignore field if parameter name (key) doesn't match
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

    # Clear the form action and save the state
    form_state['action'] = ''
    form_state_parameter.string_value = json.dumps(form_state)
    form_state_parameter.save()

    return HttpResponse(json.dumps(form_state), mimetype="appication/json")


def select_forms(datasets):
    default_form = [{'name':'default','template':'/static/publication-form/default-form.html'}]

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
                        forms.append({'name':mapping['publication_schema'],
                                      'template':mapping['form_template'],
                                      'datasets':[{'id':dataset.id,
                                                   'description':dataset.description}]})
                    else:
                        idx = next(index for (index, f) in enumerate(forms)
                                   if f['name'] == mapping['publication_schema'])
                        forms[idx]['datasets'].append({'id':dataset.id,
                                                       'description':dataset.description})
                                
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

    acl = ObjectACL(content_object=experiment,
                    pluginId=django_user,
                    entityId=str(user.id),
                    canRead=True,
                    canWrite=True,
                    canDelete=True,
                    isOwner=True,
                    aclOwnershipType=ObjectACL.OWNER_OWNED)
    acl.save()

    # Attach a "draft publication" schema
    try:
        draft_publication_schema = Schema.objects.get(
            namespace=settings.PUBLICATION_DRAFT_SCHEMA_NAMESPACE)
    except Schema.DoesNotExist:
        # Sets up the schema if it doesn't already exist.
        draft_publication_schema = Schema(namespace=settings.PUBLICATION_DRAFT_SCHEMA_NAMESPACE,
                                          name='Draft Publication',
                                          hidden=True)
        draft_publication_schema.save()
        ParameterName(schema=draft_publication_schema,name="form_state",
                      full_name="form_state").save()

    # Attach schema and blank form_state parameter
    parameter_name = ParameterName.objects.get(schema=draft_publication_schema, name="form_state")
    parameterset = ExperimentParameterSet(schema=draft_publication_schema,
                                          experiment=experiment)
    parameterset.save()
    ExperimentParameter(name=parameter_name, parameterset=parameterset).save()

    return experiment


def get_draft_publication(user, publication_id):
    for exp in Experiment.safe.owned(user):
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
            experiment_json = {'id':experiment.id,
                               'title':experiment.title,
                               'institution_name':experiment.institution_name,
                               'description':experiment.description}
            datasets = Dataset.objects.filter(experiments=experiment)
            dataset_json = []
            for dataset in datasets:
                dataset_json.append({'id':dataset.id,
                                     'description':dataset.description,
                                     'directory':dataset.directory})
            experiment_json['datasets'] = dataset_json
            json_response.append(experiment_json)
    return HttpResponse(json.dumps(json_response), mimetype="appication/json")
