# -*- coding: utf-8 -*-

#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
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

'''
forms module

.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>

'''

from os.path import basename
from UserDict import UserDict

from django import forms
from django.forms.util import ErrorList
from django.forms.models import ModelChoiceField
from django.forms.models import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.forms import ModelForm
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from haystack.forms import SearchForm

from form_utils import forms as formutils
from registration.models import RegistrationProfile

from tardis.tardis_portal import models
from tardis.tardis_portal.fields import MultiValueCommaSeparatedField
from tardis.tardis_portal.widgets import CommaSeparatedInput, Span, TextInput
from tardis.tardis_portal.models import UserProfile, UserAuthentication
from tardis.tardis_portal.auth.localdb_auth \
    import auth_key as locabdb_auth_key

from tardis.tardis_portal.ParameterSetManager import ParameterSetManager


def getAuthMethodChoices():
    authMethodChoices = ()
    for authMethods in settings.AUTH_PROVIDERS:
        authMethodChoices += ((authMethods[0], authMethods[1]),)
    return authMethodChoices


class LoginForm(AuthenticationForm):
    authMethod = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'] = \
             forms.CharField(required=True,
                             label="Username",
                             max_length=75)

        self.fields['authMethod'] = \
            forms.CharField(required=True,
                            widget=forms.Select(choices=getAuthMethodChoices()),
                            label='Authentication Method')


attrs_dict = {'class': 'required'}


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """

    username = forms.RegexField(
        regex=r'^[\w\.]+$',
        max_length=30,
        widget=forms.TextInput(attrs=attrs_dict),
        label=_("Username"),
        error_messages={'invalid':
            _("This value must contain only letters, \
            numbers and underscores.")})
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("Email address"))

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password"))

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password (again)"))

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.

        """
        username = '%s' % self.cleaned_data['username']

        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            _("A user with that username already exists."))

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and \
                'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != \
                    self.cleaned_data['password2']:
                raise forms.ValidationError(
                    _("The two password fields didn't match."))

        return self.cleaned_data

    @transaction.commit_on_success()
    def save(self, profile_callback=None):
        user = RegistrationProfile.objects.create_inactive_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'])

        userProfile = UserProfile(user=user, isDjangoAccount=True)
        userProfile.save()

        authentication = UserAuthentication(
            userProfile=userProfile,
            username=self.cleaned_data['username'],
            authenticationMethod=locabdb_auth_key)
        authentication.save()

        return user


class ChangeUserPermissionsForm(ModelForm):

    class Meta:
        from django.forms.extras.widgets import SelectDateWidget
        from tardis.tardis_portal.models import ExperimentACL
        model = ExperimentACL
        exclude = ('entityId', 'pluginId', 'experiment', 'aclOwnershipType',)
        widgets = {
            'expiryDate': SelectDateWidget(),
            'effectiveDate': SelectDateWidget()}


class ChangeGroupPermissionsForm(forms.Form):

    from django.forms.extras.widgets import SelectDateWidget

    canRead = forms.BooleanField(label='canRead', required=False)
    canWrite = forms.BooleanField(label='canWrite', required=False)
    canDelete = forms.BooleanField(label='', required=False,
                                   widget=forms.HiddenInput)

    effectiveDate = forms.DateTimeField(label='Effective Date',
            widget=SelectDateWidget(), required=False)
    expiryDate = forms.DateTimeField(label='Expiry Date',
            widget=SelectDateWidget(), required=False)


class AddUserPermissionsForm(forms.Form):

    authMethod = forms.CharField(required=True,
        widget=forms.Select(choices=getAuthMethodChoices()),
        label='Authentication Method')
    adduser = forms.CharField(label='User', required=False, max_length=100)
    adduser.widget.attrs['class'] = 'usersuggest'
    read = forms.BooleanField(label='READ', required=False, initial=True)
    read.widget.attrs['class'] = 'canRead'
    write = forms.BooleanField(label='EDIT', required=False)
    write.widget.attrs['class'] = 'canWrite'
    delete = forms.BooleanField(label='', required=False,
                                   widget=forms.HiddenInput)
    delete.widget.attrs['class'] = 'canDelete'


class AddGroupPermissionsForm(forms.Form):

    addgroup = forms.CharField(label='Group', required=False, max_length=100)
    addgroup.widget.attrs['class'] = 'groupsuggest'
    create = forms.BooleanField(label='CREATE?', required=False)
    create.widget.attrs['class'] = 'creategroup'
    authMethod = forms.CharField(required=True,
        widget=forms.Select(choices=getAuthMethodChoices()),
        label='Authentication Method')
    adduser = forms.CharField(label='User', required=False, max_length=100)
    adduser.widget.attrs['class'] = 'usersuggest'
    read = forms.BooleanField(label='READ', required=False, initial=True)
    read.widget.attrs['class'] = 'canRead'
    write = forms.BooleanField(label='EDIT', required=False)
    write.widget.attrs['class'] = 'canWrite'
    delete = forms.BooleanField(label='', required=False,
                                   widget=forms.HiddenInput)
    delete.widget.attrs['class'] = 'canDelete'


class ManageGroupPermissionsForm(forms.Form):

    authMethod = forms.CharField(required=True,
        widget=forms.Select(choices=getAuthMethodChoices()),
        label='Authentication Method')
    adduser = forms.CharField(label='User', required=False, max_length=100)
    adduser.widget.attrs['class'] = 'usersuggest'
    admin = forms.BooleanField(label='Group Admin', required=False, initial=False)
    admin.widget.attrs['class'] = 'isAdmin'


class DatafileSearchForm(forms.Form):

    filename = forms.CharField(required=False, max_length=100)


# microscopy
class MXDatafileSearchForm(DatafileSearchForm):

    __DIFFRACTOMETER_CHOICES = (
        ('-', '-'),
        ('Synchrotron', 'Synchrotron'),
        ('Rotating Anode', 'Rotating Anode'),
        ('Tube', 'Tube'))
    diffractometerType = \
        forms.CharField(widget=forms.Select(choices=__DIFFRACTOMETER_CHOICES),
        label='Diffractometer Type')
    xraySource = forms.CharField(
        required=False, label='X-ray Source', max_length=20)
    crystalName = forms.CharField(
        required=False, label='Crystal Name', max_length=20)
    resolutionLimit = forms.IntegerField(
        required=False, label='Max Resolution Limit')
    xrayWavelengthFrom = forms.IntegerField(
        required=False, label='X-ray Wavelength From',
        widget=forms.TextInput(attrs={'size': '4'})
        )
    xrayWavelengthTo = forms.IntegerField(
        required=False, label='X-ray Wavelength To',
        widget=forms.TextInput(attrs={'size': '4'})
        )


def createLinkedUserAuthenticationForm(authMethods):
    """Create a LinkedUserAuthenticationForm and use the contents of
    authMethods to the list of options in the dropdown menu for
    authenticationMethod.

    """
    _authenticationMethodChoices = ()
    for authMethodKey in authMethods.keys():
        _authenticationMethodChoices += (
            (authMethodKey, authMethods[authMethodKey]), )

    fields = {}
    fields['authenticationMethod'] = \
        forms.CharField(label='Authentication Method',
        widget=forms.Select(choices=_authenticationMethodChoices),
        required=True)
    fields['username'] = forms.CharField(label='Username',
        max_length=75, required=True)
    fields['password'] = forms.CharField(required=True,
        widget=forms.PasswordInput(), label='Password', max_length=12)

    return type('LinkedUserAuthenticationForm', (forms.BaseForm, ),
                    {'base_fields': fields})


# infrared
class IRDatafileSearchForm(DatafileSearchForm):
    pass


class ImportParamsForm(forms.Form):

    username = forms.CharField(max_length=400, required=True)
    password = forms.CharField(max_length=400, required=True)
    params = forms.FileField()


class RegisterExperimentForm(forms.Form):

    username = forms.CharField(max_length=400, required=True)
    password = forms.CharField(max_length=400, required=True)
    xmldata = forms.FileField()
    experiment_owner = forms.CharField(max_length=400, required=False)
    originid = forms.CharField(max_length=400, required=False)
    from_url = forms.CharField(max_length=400, required=False)

class Author_Experiment(forms.ModelForm):

    class Meta:
        model = models.Author_Experiment
        exclude = ('experiment',)


class FullExperimentModel(UserDict):
    """
    This is a dict wrapper that store the values returned from
    the :func:`tardis.tardis_portal.forms.FullExperiment.save` function.
    It provides a convience method for saving the model objects.
    """

    def save_m2m(self):
        """
        {'experiment': experiment,
        'author_experiments': author_experiments,
        'authors': authors,
        'datasets': datasets,
        'dataset_files': dataset_files}
        """
        self.data['experiment'].save()
        for ae in self.data['author_experiments']:
            ae.experiment = ae.experiment
            ae.save()
        for ds in self.data['datasets']:
            if not ds.immutable:
                ds.experiment = ds.experiment
                ds.save()
        for ds_f in self.data['dataset_files']:
            if not ds.immutable:
                ds_f.dataset = ds_f.dataset
                ds_f.save()

        # XXX because saving the form can be now done without
        # commit=False this won't be called during the creation
        # of new experiments.
        if hasattr(self.data['datasets'], 'deleted_forms'):
            for dataset in self.data['datasets'].deleted_forms:
                if not dataset.instance.immutable:
                    dataset.instance.delete()

        if hasattr(self.data['dataset_files'], 'deleted_forms'):
            for dataset in self.data['dataset_files'].deleted_forms:
                if not dataset.instance.immutable:
                    dataset.instance.delete()


class DataFileFormSet(BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        if 'post_save_cb' in kwargs:
            self._post_save_cb = kwargs['post_save_cb']
            del kwargs['post_save_cb']
        else:
            self._post_save_cb = None
        super(DataFileFormSet, self).__init__(**kwargs)

    def save_new(self, form, commit=True):
        #this is a local file so correct the missing details
        datafile = super(DataFileFormSet, self).save_new(form, commit=False)

        filepath = form.cleaned_data['filename']
        datafile.filename = basename(filepath)

        if not 'url' in form.cleaned_data or not form.cleaned_data['url']:
            datafile.url = filepath

        if not 'size' in form.cleaned_data or not form.cleaned_data['size']:
            datafile.size = u'0'

        if not 'protocol' in form.cleaned_data:
            datafile.protocol = u''

        if commit == True:
            datafile = super(DataFileFormSet, self).save_new(form,
                                                             commit=commit)
        return datafile

    def save_existing(self, form, instance, commit=True):
        datafile = super(DataFileFormSet, self).save_existing(form,
                                                              instance,
                                                              commit=commit)
        return datafile


class ExperimentForm(forms.ModelForm):
    """
    This handles the complex experiment forms.

    All internal datasets forms are prefixed with `dataset_`, and all
    internal dataset file fields are prefixed with `file_`. These
    are parsed out of the post data and added to the form as internal
    lists.
    """
    url = forms.CharField(required=False)

    class Meta:
        model = models.Experiment
        exclude = ('authors', 'handle', 'approved', 'created_by')

    def __init__(self, data=None, files=None, auto_id='%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, extra=0):
        self.author_experiments = []
        self.datasets = {}
        self.dataset_files = {}

        super(ExperimentForm, self).__init__(data=data,
                                             files=files,
                                             auto_id=auto_id,
                                             prefix=prefix,
                                             initial=initial,
                                             instance=instance,
                                             error_class=error_class,
                                             label_suffix=label_suffix,
                                             empty_permitted=False)

        def custom_field_cb(field):
            #if field.name == 'filename':
            #    return field.formfield(required=False)
            if field.name == 'url':
                return field.formfield(widget=Span, required=False)
            else:
                return field.formfield()

        def custom_dataset_field_cb(field):
            if field.name == 'description':
                return field.formfield(
                    widget=TextInput(attrs={'size': '80'}))
            else:
                return field.formfield()

        # initialise formsets
        if instance == None or instance.dataset_set.count() == 0:
            extra = 1
        dataset_formset = inlineformset_factory(
            models.Experiment,
            models.Dataset,
            formfield_callback=custom_dataset_field_cb,
            extra=extra, can_delete=True)

        datafile_formset = inlineformset_factory(
            models.Dataset,
            models.Dataset_File,
            formset=DataFileFormSet,
            formfield_callback=custom_field_cb,
            extra=0, can_delete=True)

        # fix up experiment form
        post_authors = self._parse_authors(data)
        self._fill_authors(post_authors)
        if instance:
            authors = instance.author_experiment_set.all()
            self.authors_experiments = [Author_Experiment(instance=a) for a
                                        in authors]
            self.initial['authors'] = ', '.join([a.author for a in authors])
            self.fields['authors'] = \
                MultiValueCommaSeparatedField([author.fields['author'] for
                                            author in self.author_experiments],
                                            widget=CommaSeparatedInput())

        # fill formsets
        self.datasets = dataset_formset(data=data,
                                        instance=instance,
                                        prefix="dataset")
        for i, df in enumerate(self.datasets.forms):
            if 'immutable' in df.initial:
                if df.initial['immutable']:
                    df.fields['description'].widget.attrs['readonly'] = True
                    df.fields['description'].editable = False
                    df.fields['immutable'].editable = False
                    df.fields['immutable'].widget.attrs['readonly'] = True

            self.dataset_files[i] = datafile_formset(data=data,
                                         instance=df.instance,
                                         prefix="ds-%s-datafile" % i)

    def _parse_authors(self, data=None):
        """
        create a dictionary containing each of the sub form types.
        """
        authors = []
        if not data:
            return authors
        if 'authors' in data:
            authors = [a.strip() for a in
                       data.get('authors').split(',')]
        return authors

    def _fill_authors(self, authors):
        if self.instance:
            o_author_experiments = \
                self.instance.author_experiment_set.all()
        else:
            o_author_experiments = []
        for num, author in enumerate(authors):
            try:
                o_ae = o_author_experiments[num]
            except IndexError:
                o_ae = models.Author_Experiment()
                o_ae.experiment = self.instance
            f = Author_Experiment(data={'author': author,
                                        'order': num},
                                  instance=o_ae)
            self.author_experiments.append(f)

        self.fields['authors'] = \
            MultiValueCommaSeparatedField([author.fields['author'] for
                                        author in self.author_experiments],
                                        widget=CommaSeparatedInput())

    def get_dataset_files(self, number):
        """
        Return a list of datafiles from a dataset

        :param number: the dataset number as identified in the form.
        :type number: integer
        :rtype: list of :class:`~tardis.tardis_portal.models.Dataset_File`
        """
        if number in self.dataset_files:
            return self.dataset_files[number]
        return []

    def get_datasets(self):
        """
        Return a tuple of datasets and associated dataset files.

        :rtype: tuple containing
         a :class:`~tardis.tardis_portal.models.Dataset`and a
         list of :class:`~tardis.tardis_portal.models.Dataset_File`
        """
        for number, form in enumerate(self.datasets.forms):
            yield (form, self.get_dataset_files(number))

    def save(self, commit=True):
        # remove m2m field before saving
        del self.cleaned_data['authors']

        experiment = super(ExperimentForm, self).save(commit)

        authors = []
        author_experiments = []
        datasets = []
        dataset_files = []

        for ae in self.author_experiments:
            ae.instance.experiment = ae.instance.experiment
            o_ae = ae.save(commit=commit)
            author_experiments.append(o_ae)
        for key, dataset in enumerate(self.datasets.forms):
            if dataset not in self.datasets.deleted_forms:
                # XXX for some random reason the link between
                # the instance needs
                # to be reinitialised
                dataset.instance.experiment = experiment
                o_dataset = dataset.save(commit)
                datasets.append(o_dataset)
                # save any datafiles if the data set has any
                mutable = True
                if 'immutable' in dataset.initial:
                    if dataset.initial['immutable']:
                        mutable = False

                if self.dataset_files[key] and mutable:
                    o_df = self.dataset_files[key].save(commit)
                    dataset_files += o_df

        if hasattr(self.datasets, 'deleted_forms'):
            for ds in self.datasets.deleted_forms:
                if not ds.instance.immutable:
                    ds.instance.delete()

        if hasattr(self.dataset_files, 'deleted_forms'):
            for df in self.dataset_files.deleted_forms:
                if not ds.instance.immutable:
                    df.instance.delete()

        return FullExperimentModel({'experiment': experiment,
                                    'author_experiments': author_experiments,
                                    'authors': authors,
                                    'datasets': datasets,
                                    'dataset_files': dataset_files})

    def is_valid(self):
        """
        Test the validity of the form, the form may be invalid even if the
        error attribute has no contents. This is because the returnd value
        is dependent on the validity of the nested forms.

        This validity also takes into account forign keys that might be
        dependent on an unsaved model.

        :rtype: bool
        """
        if self.is_bound and bool(self.errors):
            return not bool(self.errors)

        # TODO since this is a compound field, this should merge the errors
        for ae in self.author_experiments:
            for name, error in ae.errors.items():
                if isinstance(ae.fields[name], ModelChoiceField):
                    continue
                if ae.is_bound and bool(ae.errors[name]):
                    return False

        for dataset, files in self.get_datasets():
            for name, error in dataset.errors.items():
                if isinstance(dataset.fields[name], ModelChoiceField):
                    continue
                if dataset.is_bound and bool(dataset.errors[name]):
                    return False
        return True


def createSearchDatafileForm(searchQueryType):

    from errors import UnsupportedSearchQueryTypeError
    from tardis.tardis_portal.models import ParameterName

    parameterNames = None

    if searchQueryType in models.Schema.getSubTypes():
        parameterNames = \
            ParameterName.objects.filter(
            schema__namespace__in=models.Schema.getNamespaces(
            models.Schema.DATAFILE, searchQueryType) +
            models.Schema.getNamespaces(models.Schema.DATASET,
            searchQueryType), is_searchable='True')

        fields = {}

        fields['filename'] = forms.CharField(label='Filename',
                max_length=100, required=False)
        fields['type'] = forms.CharField(widget=forms.HiddenInput,
                initial=searchQueryType)

        for parameterName in parameterNames:
            if parameterName.data_type == ParameterName.NUMERIC:
                if parameterName.comparison_type \
                    == ParameterName.RANGE_COMPARISON:
                    fields[parameterName.name + 'From'] = \
                        forms.DecimalField(label=parameterName.full_name
                            + ' From', required=False)
                    fields[parameterName.name + 'To'] = \
                        forms.DecimalField(label=parameterName.full_name
                            + ' To', required=False)
                else:
                    # note that we'll also ignore the choices text box entry
                    # even if it's filled if the parameter is of numeric type
                    # TODO: decide if we are to raise an exception if
                    #       parameterName.choices is not empty
                    fields[parameterName.name] = \
                        forms.DecimalField(label=parameterName.full_name,
                            required=False)
            else:  # parameter is a string
                if parameterName.choices != '':
                    fields[parameterName.name] = \
                        forms.CharField(label=parameterName.full_name,
                        widget=forms.Select(choices=__getParameterChoices(
                        parameterName.choices)), required=False)
                else:
                    fields[parameterName.name] = \
                        forms.CharField(label=parameterName.full_name,
                        max_length=255, required=False)

        return type('SearchDatafileForm', (forms.BaseForm, ),
                    {'base_fields': fields})
    else:
        raise UnsupportedSearchQueryTypeError(
            "'%s' search query type is currently unsupported" %
            (searchQueryType, ))


def createSearchExperimentForm():

    from django.forms.extras.widgets import SelectDateWidget
    from tardis.tardis_portal.models import ParameterName

    fields = {}

    fields['title'] = forms.CharField(label='Title',
            max_length=20, required=False)
    fields['description'] = forms.CharField(label='Experiment Description',
            max_length=20, required=False)
    fields['institutionName'] = forms.CharField(label='Institution Name',
            max_length=20, required=False)
    fields['creator'] = forms.CharField(label='Author\'s Name',
            max_length=20, required=False)
    fields['date'] = forms.DateTimeField(label='Experiment Date',
            widget=SelectDateWidget(), required=False)

    fieldsets = [('main fields', {'fields': ['title', 'description', 'institutionName', 'creator', 'date']})] 

    schemaAndFieldLists = []

    experimentSchemata = models.Schema.objects.filter(type=models.Schema.EXPERIMENT)
    for schema in experimentSchemata:
        searchableParameterNames = \
            schema.parametername_set.filter(is_searchable=True)
        fieldNames = []
        schemaAndFieldLists.append((schema, fieldNames))
        for parameterName in searchableParameterNames:
            if parameterName.data_type == ParameterName.NUMERIC:
                if parameterName.comparison_type \
                    == ParameterName.RANGE_COMPARISON:
                    fields[parameterName.name + 'From'] = \
                        forms.DecimalField(label=parameterName.full_name
                            + ' From', required=False)
                    fields[parameterName.name + 'To'] = \
                        forms.DecimalField(label=parameterName.full_name
                            + ' To', required=False)
                    fieldNames.append(parameterName.name + 'From')
                    fieldNames.append(parameterName.name + 'To')
                else:
                    # note that we'll also ignore the choices text box entry
                    # even if it's filled if the parameter is of numeric type
                    # TODO: decide if we are to raise an exception if
                    #       parameterName.choices is not empty
                    fields[parameterName.name] = \
                        forms.DecimalField(label=parameterName.full_name,
                            required=False)
                    fieldNames.append(parameterName.name)
            else:  # parameter is a string
                if parameterName.choices != '':
                    fields[parameterName.name] = \
                        forms.CharField(label=parameterName.full_name,
                        widget=forms.Select(choices=__getParameterChoices(
                        parameterName.choices)), required=False)
                else:
                    fields[parameterName.name] = \
                        forms.CharField(label=parameterName.full_name,
                        max_length=255, required=False)
                fieldNames.append(parameterName.name)


    for schema, fieldlist in schemaAndFieldLists:
        name = schema.name if schema.name != None else 'No schema name'
        fieldsets.append((name, {'fields': fieldlist}))

    return type('SearchExperimentForm', (formutils.BetterBaseForm, forms.BaseForm, ),
                    {'base_fields': fields, 'base_fieldsets': fieldsets,
                     'base_row_attrs': {}})


def __getParameterChoices(choicesString):
    """Handle the choices string in this format:
    '(hello:hi how are you), (yes:i am here), (no:joe)'

    Note that this parser is very strict and is not smart enough to handle
    any extra unknown characters that the user might put in the choices
    textbox.

    """

    import string
    import re
    paramChoices = ()

    # we'll always add '-' as the default value for a dropdown menu just
    # incase the user doesn't specify a value they'd like to search for
    paramChoices += (('-', '-'),)
    dropDownEntryPattern = re.compile(r'\((.*):(.*)\)')

    dropDownEntryStrings = string.split(choicesString, ',')
    for dropDownEntry in dropDownEntryStrings:
        dropDownEntry = string.strip(dropDownEntry)
        (key, value) = dropDownEntryPattern.search(dropDownEntry).groups()
        paramChoices += ((str(key), str(value)),)

    return paramChoices


def createSearchDatafileSelectionForm(initial=None):

    supportedDatafileSearches = (('-', 'Datafile'),)
    for key in models.Schema.getSubTypes():
        supportedDatafileSearches += ((key, key.upper()),)

    fields = {}
    fields['type'] = \
        forms.CharField(label='type',
        widget=forms.Select(choices=supportedDatafileSearches),
        required=False, initial=initial)
    fields['type'].widget.attrs['class'] = 'searchdropdown'
    return type('DatafileSelectionForm', (forms.BaseForm, ),
                    {'base_fields': fields})


class NoInput(forms.Widget):

    def render(self, name, value, attrs=None):
        from django.utils.safestring import mark_safe
        return mark_safe(value)


class StaticField(forms.Field):

    widget = NoInput

    def clean(self, value):
        return


def create_parameterset_edit_form(
    parameterset,
    request=None):

    from tardis.tardis_portal.models import ParameterName

    # if POST data to save
    if request:
        from django.utils.datastructures import SortedDict
        fields = SortedDict()

        for key, value in sorted(request.POST.iteritems()):

            x = 1

            stripped_key = key.replace('_s47_', '/')
            stripped_key = stripped_key.rpartition('__')[0]

            parameter_name = ParameterName.objects.get(
                schema=parameterset.schema,
                name=stripped_key)

            units = ""
            if parameter_name.units:
                units = " (" + parameter_name.units + ")"
                # if not valid, spit back as exact
                if parameter_name.isNumeric():
                    fields[key] = \
                        forms.DecimalField(label=parameter_name.full_name + units,
                                           required=False,
                                           initial=value)
                else:
                    fields[key] = \
                        forms.CharField(label=parameter_name.full_name + units,
                                        max_length=255, required=False,
                                        initial=value)

        return type('DynamicForm', (forms.BaseForm, ), {'base_fields': fields})

    else:
        from django.utils.datastructures import SortedDict
        fields = SortedDict()
        psm = ParameterSetManager(parameterset=parameterset)

        for dfp in psm.parameters:

            x = 1

            form_id = dfp.name.name + "__" + str(x)

            while form_id in fields:
                x = x + 1
                form_id = dfp.name.name + "__" + str(x)

            units = ""
            if dfp.name.units:
                units = " (" + dfp.name.units + ")"

            form_id = form_id.replace('/', '_s47_')

            if dfp.name.isNumeric():
                fields[form_id] = \
                    forms.DecimalField(label=dfp.name.full_name + units,
                                       required=False,
                                       initial=dfp.numerical_value)
            else:
                fields[form_id] = \
                    forms.CharField(label=dfp.name.full_name + units,
                                    max_length=255,
                                    required=False,
                                    initial=dfp.string_value)

            if dfp.name.immutable:
                fields[form_id].widget.attrs['readonly'] = 'readonly'

        return type('DynamicForm', (forms.BaseForm, ),
                    {'base_fields': fields})


def save_datafile_edit_form(parameterset, request):

    psm = ParameterSetManager(parameterset=parameterset)

    psm.delete_all_params()

    for key, value in sorted(request.POST.iteritems()):
        if value:
            stripped_key = key.replace('_s47_', '/')
            stripped_key = stripped_key.rpartition('__')[0]

            psm.new_param(stripped_key, value)


def create_datafile_add_form(
    schema, parentObject,
    request=None):

    from tardis.tardis_portal.models import ParameterName

    # if POST data to save
    if request:
        from django.utils.datastructures import SortedDict
        fields = SortedDict()

        for key, value in sorted(request.POST.iteritems()):

            x = 1

            stripped_key = key.replace('_s47_', '/')
            stripped_key = stripped_key.rpartition('__')[0]

            parameter_name = ParameterName.objects.get(
                schema__namespace=schema,
                name=stripped_key)

            units = ""
            if parameter_name.units:
                units = " (" + parameter_name.units + ")"

            # if not valid, spit back as exact
            if parameter_name.isNumeric():
                fields[key] = \
                    forms.DecimalField(label=parameter_name.full_name + units,
                                       required=False,
                                       initial=value,
                                       )
            else:
                fields[key] = \
                    forms.CharField(label=parameter_name.full_name + units,
                                    max_length=255, required=False,
                                    initial=value,
                                    )

        return type('DynamicForm', (forms.BaseForm, ), {'base_fields': fields})

    else:
        from django.utils.datastructures import SortedDict
        fields = SortedDict()

        parameternames = ParameterName.objects.filter(
            schema__namespace=schema).order_by('name')

        for dfp in parameternames:

            x = 1

            form_id = dfp.name + "__" + str(x)

            while form_id in fields:
                x = x + 1
                form_id = dfp.name + "__" + str(x)

            units = ""
            if dfp.units:
                units = " (" + dfp.units + ")"

            form_id = form_id.replace('/', '_s47_')

            if dfp.isNumeric():
                fields[form_id] = \
                forms.DecimalField(label=dfp.full_name + units,
                required=False)
            else:
                fields[form_id] = \
                forms.CharField(label=dfp.full_name + units,
                max_length=255, required=False)

        return type('DynamicForm', (forms.BaseForm, ),
            {'base_fields': fields})


def save_datafile_add_form(schema, parentObject, request):

    psm = ParameterSetManager(schema=schema,
        parentObject=parentObject)

    for key, value in sorted(request.POST.iteritems()):
        if value:
            stripped_key = key.replace('_s47_', '/')
            stripped_key = stripped_key.rpartition('__')[0]

            psm.new_param(stripped_key, value)

class RawSearchForm(SearchForm):
    
    def search(self):
        #self.clean()
        sqs = self.searchqueryset.raw_search(self.cleaned_data['q'])

        if self.load_all:
            sqs.load_all()

        return sqs
