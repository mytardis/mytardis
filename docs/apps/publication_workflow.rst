=================
Publication Forms
=================

Introduction
============
MyTardis supports a simple, configurable, publication workflow allowing
researchers to curate collections of data sets for public release. This
workflow represents an alternative to simply setting an experiment to
"public access" that encourages researchers to provide a higher standard of
metadata and bibliographic information, including authorship and
acknowledgements without altering the original experiment. Additional
features include embargo support, admin publication approvals, and PDB
metadata extraction from the Protein Data Bank. DOI minting is also
supported but depends on a `third-party DOI minting service
<https://github.com/monash-merc/modc-doi>`_. Set up of the minting service
is beyond the scope of this document.

The publication workflow is a three-stage process:

 1. The user selects data sets to include in the publication, along with a
    title and description
 2. Based on the selected data sets, domain-specific fields are presented
 3. Authorship, acknowledgements and embargo information is collected

After stage one is started, the publication remains in draft until it is
submitted.

Under the hood, this is achieved by creating a new experiment object that is
differentiated from regular experiments by attaching a special publication
schema. This new experiment links to the selected data sets, which may be
from one or many original experiments. Publication related tasks (e.g.
embargo processing) filter based on the publication schema and act accordingly.

Basic setup
===========
A minimum setup requires the :py:mod:`tardis.apps.publication_workflow` app to
be added to :py:const:`INSTALLED_APPS` and the following settings to be
defined:

 * :py:const:`PUBLICATION_DATA_ADMIN` set to the user name of the person
   responsible for research data management
 * :py:const:`PUBLICATION_NOTIFICATION_SENDER_EMAIL` set to the email from
   which publication related notifications should be sent
 * :py:const:`PUBLICATION_INTRODUCTION` set to an HTML formatted
   introductory text that is displayed to the user before begins the
   publication process
 * the :py:mod:`apps.publication_workflow.update_publication_records` task
   should be added to :py:const:`CELERYBEAT_SCHEDULE` and set to a
   reasonable interval for embargo processing

To disable the approval workflow and have publications automatically
released, :py:const:`PUBLICATIONS_REQUIRE_APPROVAL` can be set to False
(defaults to True).

DOI support
-----------
These additional settings are required for DOI minting support:

 * :py:const:`MODC_DOI_ENABLED` set to True to enable support
 * :py:const:`MODC_DOI_API_ID` set to the API id assigned to this app by the
   minting service
 * :py:const:`MODC_DOI_API_PASSWORD` set to the password corresponding to
   the API id
 * :py:const:`MODC_DOI_MINT_DEFINITION` set to the WSDL file for DOI minting
 * :py:const:`MODC_DOI_ACTIVATE_DEFINITION` set to the WSDL file for DOI
   activation
 * :py:const:`MODC_DOI_DEACTIVATE_DEFINITION` set to the WSDL file for DOI
   deactivation
 * :py:const:`MODC_DOI_ENDPOINT` set to the API SOAP endpoint
 * :py:const:`MODC_DOI_MINT_URL_ROOT` set to the URL root for registered
 DOIs, e.g. *http://tardis.example.com/*

Email configuration
===================
There are a number of different notifications that are sent during the
publication process. Very basic templates are preconfigured, but may be
overridden by defining the :py:const:`PUBLICATION_EMAIL_MESSAGES` dictionary
in the *settings.py* file. Review the *default_settings.py* file for this
app to see defaults. The following keys in the dictionary must be defined if
 overriding the defaults:

 * :py:const:`PUBLICATION_DATA_ADMIN['requires_authorisation']`
    * Sent to publication admins to authorise/approve a publication for release
    * `{user_name}`: the submitting user's user name
    * `{pub_url}`: the direct link to the publication for review
    * `{approvals_url}`: the link to the admin approvals page
 * :py:const:`PUBLICATION_DATA_ADMIN['awaiting_approval']`
    * Sent to all authors immediately after submission
    * `{pub_title}`: the title of the publication
 * :py:const:`PUBLICATION_DATA_ADMIN['approved']`
    * Sent to all authors after the publication has been approved but before
      being released (e.g. by embargo expiry)
    * `{pub_title}`: the title of the publication
    * `{pub_url}`: the direct link to the publication
 * :py:const:`PUBLICATION_DATA_ADMIN['approved_with_doi']`
    * As above, but contains a DOI
    * `{doi}`: the publication's DOI
 * :py:const:`PUBLICATION_DATA_ADMIN['rejected']`
    * Sent to all authors if the publication is rejected
    * `{pub_title}`: the title of the publication
 * :py:const:`PUBLICATION_DATA_ADMIN['reverted_to_draft']`
    * Sent to all authors when the publication requires amendments by the
      submitting user
    * `{pub_title}`: the title of the publication
 * :py:const:`PUBLICATION_DATA_ADMIN['released']`
    * Sent to all authors when the publication has been released following
      approval
    * `{pub_title}`: the title of the publication
 * :py:const:`PUBLICATION_DATA_ADMIN['released_with_doi']`
    * As above, but contains a DOI
    * `{doi}`: the publication's DOI

Domain-specific metadata
========================
Domain-specific metadata is collected in stage two of the publication
process. The forms to display are determined by inspecting the attached
data set schemas. Schema to form mappings are defined in the
:py:const:`PUBLICATION_FORM_MAPPINGS` setting, an example of which is shown
below:

.. code-block:: python

   PUBLICATION_FORM_MAPPINGS = [
    {'dataset_schema': r'^http://synchrotron.org.au/mx/',
     'publication_schema': PDB_PUBLICATION_SCHEMA_ROOT,
     'form_template': '/static/publication-form/mx-pdb-template.html'},
    {'dataset_schema': r'^http://synchrotron.org.au/mx/',
     'publication_schema': MX_PUBLICATION_DATASET_SCHEMA,
     'form_template':
         '/static/publication-form/mx-dataset-description-template.html'}]

`dataset_schema` is a regular expression applied to each schema attached to
each data set, and if matched, the corresponding `publication_schema` is added
to the resulting publication, and its parameters are provided by the form
template. Care could be taken in constructing the `dataset_schema` regex
keeping in mind that the expression could match one or more data sets.

Constructing the form template HTML files are somewhat challenging;
examples are provided in the `static/publication-form` directory. These
forms require special syntax that is defined using *AngularJs*. All forms
have access to a `formTemplate` variable, which includes the publication
schema name (`formTemplate.name`) a list of affected data sets
(*formTemplate.datasets*). Each form will populate `formData.extraInfo[x]`
with the user supplied data, where `x` is a unique key.

The forms themselves must be enclosed in a `<tardis-form>` tag, which requires
a `my-model` attribute (set to `formData.extraInfo[x]`, and a *schema* (set
to `formTemplate.name`). Any form field tags must also include the
*tardis-form-field* attribute, in addition to `parameter-name`, which is set
to the publication schema's parameter to populate. The value given to `x` as
the `formData.extraInfo[x]` key must be unique over all included forms. In
our example below, the form and data set indices are concatenated to form
this unique key. Each entry in `formData.extraInfo` is given its own
parameter set in the final publication metadata.

Here is an example that collects some information for each dataset that
matches the `dataset_schema` regex:

.. code-block:: html

   <div ng-repeat="ds in formTemplate.datasets"
        ng-init="f = $parent.$index; formData.extraInfo[f+'.'+$index]['dataset'] = ds.description;">
        <h4>{{ ds.description }}</h4>
        <tardis-form my-model="formData.extraInfo[f+'.'+$index]" schema="formTemplate.name">
	         <textarea tardis-form-field parameter-name="additional-information"
                       rows="3"
                       style="width:100%;"
                       placeholder="Information about this dataset.">
             </textarea>
        </tardis-form>
   </div>

The above form works as follows:

 1. The code inside the outer `<div>` tag is repeated for each data set, which
    is provided by `formTemplate.datasets`. The outer `<div>` tag also
    initialises a form index, `f`, obtained from the parent scope's `$index`
    variable, which is used in conjunction with the inner scope's `$index`
    variable to form the unique key for `formData.extraInfo`; namely,
    `formData.extraInfo[f+'.'+$index]`.
 2. `ng-init` in the outer `<div>` tag also saves a 'dataset' field, which is
    included in `formData.extraInfo`. This functions exactly as a hidden
    HTML input field would.
 3. The corresponding dataset name is displayed to the user in the <h4> tag
 4. A `<tardis-form>` is started, using `formData.extraInfo[f+'.'+$index]` as
    its model, linking it to the schema provided by `formTemplate.name`.
 5. A `<textarea>` collects a data set description that will be added to the
    parameter named 'additional-information', as defined in the
    corresponding schema

Please note that it is extremely important to ensure that the
`parameter-name` attribute for each form field matches exactly the schema
parameter. Any fields that do not match are silently ignored!
