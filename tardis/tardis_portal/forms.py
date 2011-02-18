# -*- coding: utf-8 -*-

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

from registration.models import RegistrationProfile

from tardis.tardis_portal import models
from tardis.tardis_portal.fields import MultiValueCommaSeparatedField
from tardis.tardis_portal.widgets import CommaSeparatedInput, Span
from tardis.tardis_portal.models import UserProfile, UserAuthentication
from tardis.tardis_portal.auth.localdb_auth \
    import auth_key as locabdb_auth_key


class LoginForm(AuthenticationForm):
    authMethod = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'] = \
             forms.CharField(required=True,
                             label="Username",
                             max_length=75)

        authMethodChoices = ()
        for authMethods in settings.AUTH_PROVIDERS:
            authMethodChoices += ((authMethods[0], authMethods[1]),)

        self.fields['authMethod'] = \
            forms.CharField(required=True,
                            widget=forms.Select(choices=authMethodChoices),
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
        max_length=31 - len(locabdb_auth_key),  # 31, max pw len with _ char
        widget=forms.TextInput(attrs=attrs_dict),
        label=_("Username"),
        error_messages={'invalid':
                            _("This value must contain only letters, numbers and underscores.")})
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
        username = '%s_%s' % (locabdb_auth_key, self.cleaned_data['username'])

        try:
            user = User.objects.get(username__iexact=username)
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
            username=self.cleaned_data['username'].split(locabdb_auth_key)[1],
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
    canDelete = forms.BooleanField(label='canDelete', required=False)

    effectiveDate = forms.DateTimeField(label='Effective Date',
            widget=SelectDateWidget(), required=False)
    expiryDate = forms.DateTimeField(label='Expiry Date',
            widget=SelectDateWidget(), required=False)


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
        widget=forms.TextInput(attrs={'size': '4'}))
    xrayWavelengthTo = forms.IntegerField(
        required=False, label='X-ray Wavelength To',
        widget=forms.TextInput(attrs={'size': '4'}))


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


class EquipmentSearchForm(forms.Form):

    key = forms.CharField(label='Short Name',
        max_length=30, required=False)
    description = forms.CharField(label='Description',
        required=False)
    make = forms.CharField(label='Make', max_length=60, required=False)
    model = forms.CharField(label='Model', max_length=60, required=False)
    type = forms.CharField(label='Type', max_length=60, required=False)
    serial = forms.CharField(label='Serial No', max_length=60, required=False)


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
            ds.experiment = ds.experiment
            ds.save()
        for ds_f in self.data['dataset_files']:
            ds_f.dataset = ds_f.dataset
            ds_f.save()

        # XXX because saving the form can be now done without
        # commit=False this won't be called during the creation
        # of new experiments.
        if hasattr(self.data['datasets'], 'deleted_forms'):
            for dataset in self.data['datasets'].deleted_forms:
                dataset.instance.delete()
        if hasattr(self.data['dataset_files'], 'deleted_forms'):
            for dataset in self.data['dataset_files'].deleted_forms:
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
        # this is a local file so correct the missing details
        datafile = super(DataFileFormSet, self).save_new(form, commit=False)

        filepath = form.cleaned_data['filename']
        datafile.filename = basename(filepath)

        if not 'url' in form.cleaned_data or not form.cleaned_data['url']:
            datafile.url = 'file://' + filepath

        if not 'size' in form.cleaned_data or not form.cleaned_data['size']:
            datafile.size = u'0'

        if not 'protocol' in form.cleaned_data:
            datafile.protocol = u''

        if commit == True:
            datafile = super(DataFileFormSet, self).save_new(form,
                                                             commit=commit)
        if self._post_save_cb:
            self._post_save_cb(datafile, True)
        return datafile

    def save_existing(self, form, instance, commit=True):
        datafile = super(DataFileFormSet, self).save_existing(form,
                                                              instance,
                                                              commit=commit)
        if self._post_save_cb:
            self._post_save_cb(datafile, False)
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
                 empty_permitted=False, instance=None, extra=0,
                 datafile_post_save_cb=None):
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
            if field.name == 'url':
                return field.formfield(required=False)
            elif field.name == 'filename':
                return field.formfield(widget=Span)
            else:
                return field.formfield()

        # initialise formsets
        dataset_formset = inlineformset_factory(models.Experiment,
                                                models.Dataset,
                                                extra=extra, can_delete=True)
        datafile_formset = inlineformset_factory(models.Dataset,
                                                 models.Dataset_File,
                                                 formset=DataFileFormSet,
                                                 formfield_callback=custom_field_cb,
                                                 extra=0, can_delete=True)

        # fix up experiment form
        post_authors = self._parse_authors(data)
        self._fill_authors(post_authors)
        if instance:
            authors = instance.author_experiment_set.all()
            self.authors_experiments = [Author_Experiment(instance=a) for a in authors]
            self.initial['authors'] = ', '.join([a.author for a in authors])
            self.fields['authors'] = \
                MultiValueCommaSeparatedField([author.fields['author'] for author in self.author_experiments],
                                              widget=CommaSeparatedInput())

        # fill formsets
        self.datasets = dataset_formset(data=data,
                                        instance=instance,
                                        prefix="dataset")
        for i, df in enumerate(self.datasets.forms):
            self.dataset_files[i] = datafile_formset(data=data,
                                                     instance=df.instance,
                                                     post_save_cb=datafile_post_save_cb,
                                                     prefix="dataset-%s-datafile" % i)

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
            MultiValueCommaSeparatedField([author.fields['author'] for author in self.author_experiments],
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
            # XXX for some random reason the link between the instance needs
            # to be reinitialised
            dataset.instance.experiment = experiment
            o_dataset = dataset.save(commit)
            datasets.append(o_dataset)
            # save any datafiles if the data set has any
            if self.dataset_files[key]:
                o_df = self.dataset_files[key].save(commit)
                dataset_files += o_df

        if hasattr(self.datasets, 'deleted_forms'):
            for ds in self.datasets.deleted_forms:
                ds.instance.delete()

        if hasattr(self.dataset_files, 'deleted_forms'):
            for df in self.dataset_files.deleted_forms:
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
    from tardis.tardis_portal import constants

    parameterNames = None

    if searchQueryType in constants.SCHEMA_DICT:
        parameterNames = \
            ParameterName.objects.filter(
            schema__namespace__in=[constants.SCHEMA_DICT[searchQueryType]\
            ['datafile'], constants.SCHEMA_DICT[searchQueryType]['dataset']],
            is_searchable='True')

        fields = {}

        fields['filename'] = forms.CharField(label='Filename',
                max_length=100, required=False)
        fields['type'] = forms.CharField(widget=forms.HiddenInput,
                initial=searchQueryType)

        for parameterName in parameterNames:
            if parameterName.is_numeric:
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
    from tardis.tardis_portal import constants

    parameterNames = []

    for experimentSchema in constants.EXPERIMENT_SCHEMAS:
        parameterNames += \
            ParameterName.objects.filter(
            schema__namespace__iexact=experimentSchema,
            is_searchable='True')

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

    for parameterName in parameterNames:
        if parameterName.is_numeric:
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

    return type('SearchExperimentForm', (forms.BaseForm, ),
                    {'base_fields': fields})


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


def createSearchDatafileSelectionForm():

    from tardis.tardis_portal import constants

    supportedDatafileSearches = (('-', 'Datafile'),)
    for key in constants.SCHEMA_DICT:
        supportedDatafileSearches += ((key, key.upper()),)

    fields = {}
    fields['type'] = \
        forms.CharField(label='type',
        widget=forms.Select(choices=supportedDatafileSearches),
        required=False)
    fields['type'].widget.attrs['class'] = 'searchdropdown'

    return type('DatafileSelectionForm', (forms.BaseForm, ),
                    {'base_fields': fields})
