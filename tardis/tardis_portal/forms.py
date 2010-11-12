#!/usr/bin/env python
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

@author: Gerson Galang
'''

import re
from os.path import basename

from django import forms
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import ErrorDict, ErrorList
from django.forms.models import ModelChoiceField
from django.forms.forms import BoundField

from tardis.tardis_portal import models
from tardis.tardis_portal.fields import MultiValueCommaSeparatedField
from tardis.tardis_portal.widgets import CommaSeparatedInput, Label, Span


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


class PostfixedBoundField(BoundField):
    def _auto_attrs(self, attrs=None):
        if not hasattr(self.form, 'postfix'):
            return attrs

        if not attrs:
            attrs = {}

        attrs.update({'id': self.form.auto_id % self.name +
                      getattr(self.form, 'postfix'),
                      'name': self.form.auto_id % self.name +
                      getattr(self.form, 'postfix')})

        return attrs

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Renders the field by rendering the passed widget, adding any HTML
        attributes passed as attrs.  If no widget is specified, then the
        field's default widget will be used.
        """
        return super(PostfixedBoundField, self).as_widget(
            widget=widget,
            attrs=self._auto_attrs(attrs),
            only_initial=only_initial)

    def __unicode__(self):
        """Renders this field as an HTML widget."""
        if self.field.show_hidden_initial:
            return self.as_widget() + self.as_hidden(only_initial=True)
        return self.as_widget(attrs=self._auto_attrs())

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def as_label(self, attrs=None, **kwargs):
        """
        Returns a string of HTML for representing this as an <label></label>.
        """
        return self.as_widget(Label(), attrs=self._auto_attrs(attrs), **kwargs)

    def as_span(self, attrs=None, **kwargs):
        """
        Returns a string of HTML for representing this as an <span></span>.
        """
        return self.as_widget(Span(), attrs=self._auto_attrs(attrs), **kwargs)


class PostfixedForm:
    def __iter__(self):
        for name, field in self.fields.items():
            yield PostfixedBoundField(self, field, name)

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)
        return PostfixedBoundField(self, field, name)

    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []

        for name, field in self.fields.items():
            html_class_attr = ''
            bf = PostfixedBoundField(self, field, name)
            bf_errors = self.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
                hidden_fields.append(unicode(bf))
            else:
                # Create a 'class="..."' atribute if the row should have any
                # CSS classes applied.
                css_classes = bf.css_classes()
                if css_classes:
                    html_class_attr = ' class="%s"' % css_classes

                if errors_on_separate_row and bf_errors:
                    output.append(error_row % force_unicode(bf_errors))

                if bf.label:
                    label = conditional_escape(force_unicode(bf.label))
                    # Only add the suffix if the label does not end in
                    # punctuation.
                    if self.label_suffix:
                        if label[-1] not in ':?.!':
                            label += self.label_suffix
                    label = bf.label_tag(label) or ''
                else:
                    label = ''

                if field.help_text:
                    help_text = help_text_html % force_unicode(field.help_text)
                else:
                    help_text = u''

                output.append(normal_row % {
                    'errors': force_unicode(bf_errors),
                    'label': force_unicode(label),
                    'field': unicode(bf),
                    'help_text': help_text,
                    'html_class_attr': html_class_attr
                })

        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))

        if hidden_fields: # Insert any hidden fields in the last row.
            str_hidden = u''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {'errors': '', 'label': '',
                                              'field': '', 'help_text':'',
                                              'html_class_attr': html_class_attr})
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe(u'\n'.join(output))


class Author_Experiment(forms.ModelForm):
    class Meta:
        model = models.Author_Experiment


class Author(forms.ModelForm):
    class Meta:
        model = models.Author


class Dataset(PostfixedForm, forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    # XXX Probably should be an InlineForignKeyField
    experiment = forms.ModelChoiceField(
        queryset=models.Experiment.objects.all(),
        widget=forms.HiddenInput())

    class Meta:
        model = models.Dataset


class Dataset_File(PostfixedForm, forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    # XXX Probably should be an InlineForignKeyField
    dataset = forms.ModelChoiceField(queryset=models.Dataset.objects.all(),
                                     widget=forms.HiddenInput())

    class Meta:
        model = models.Dataset_File


class Experiment(forms.ModelForm):
    class Meta:
        model = models.Experiment
        exclude = ('authors', 'handle', 'approved')


class FullExperiment(Experiment):
    """
    This handles the complex experiment forms.

    The post format is expected to be like::

        abstract Test
        authors Mr Bob
        dataset_description[0] 1
        dataset_description[2] 2
        dataset_description[3] 3
        file_filename[0] 2R9Y/downloadFiles.py
        file_filename[0] 2R9Y/Images/0510060001.osc
        file_filename[0] 2R9Y/Images/0510060002.osc
        file_filename[2] 2R9Y/downloadFiles.py
        file_filename[3] 2R9Y/downloadFiles.py
        file_filename[3] 2R9Y/toplevel.log
        title Test Title

    All internal datasets forms are prefixed with `dataset_`, and all
    internal dataset file fields are prefixed with `file_`. These
    are parsed out of the post data and added to the form as internal
    lists.

    """
    re_post_data = re.compile('(?P<form>[^_]*)_(?P<field>.*)\[(?P<number>[\d]+)\]$')
    dataset_field_translation = {"description": "dataset_description"}
    base_fields = {}

    def __init__(self, data=None, files=None, auto_id='%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, extra=1):
        self.authors = []
        self.datasets = {}
        self.dataset_files = {}
        self.__exp_fields = {}
        self.__ds_num = 0

        super(FullExperiment, self).__init__(data=data,
                                             files=files,
                                             auto_id=auto_id,
                                             prefix=prefix,
                                             initial=initial,
                                             instance=instance,
                                             error_class=error_class,
                                             label_suffix=label_suffix,
                                             empty_permitted=False)

        initial = self._parse_initial(initial)
        post_data = self._parse_post(data)

        if data:
            self._fill_forms(post_data, initial)
        else:
            self._fill_forms(post_data, initial)
            self._initialise_from_instance(instance)
            # TODO, needs to start counting from where parse_form stops
            if not self.datasets:
                for i in xrange(self.__ds_num, extra):
                    self._add_dataset_form(i, Dataset(auto_id='dataset_%s'))

    def _initialise_from_instance(self, experiment):
        """
        Format an instance of an
        :class:`~tardis.tardis_portal.models.Experiment` model initialise
        the internal form variables.

        :param experiment: maximum number of stack frames to show
        :type experiment: :class:`tardis.tardis_portal.models.Experiment`
        :rtype: dictionary containing strings and lists of strings
        """
        if not experiment:
            return
        authors = experiment.authors.all()
        self.authors = [Author(instance=a) for a in authors]
        self.initial['authors'] = ', '.join([a.name for a in authors])
        self.fields['authors'] = \
            MultiValueCommaSeparatedField([author.fields['name'] for author in self.authors],
                                          widget=CommaSeparatedInput())

        for i, ds in enumerate(experiment.dataset_set.all()):
            form = Dataset(instance=ds, auto_id='dataset_%s')
            self._add_dataset_form(i, form)

            self.dataset_files[i] = []
            for file in ds.dataset_file_set.all():
                self._add_datafile_form(i, Dataset_File(instance=file,
                                                        auto_id='file_%s'))

    def _parse_initial(self, initial=None):
        """
        create a dictionary containing each of the sub form types.
        """
        parsed = {'experiment': {}, 'authors': {},
                  'dataset': {}, 'file': {}}
        if not initial:
            return parsed
        if 'authors' in initial:
            parsed['authors'] = initial['authors']
        for k, v in initial.items():
            m = self.re_post_data.match(k)
            if m:
                item = m.groupdict()
                field = item['field']
                if not item['number'] in parsed[item['form']]:
                    parsed[item['form']][item['number']] = {}
                parsed[item['form']][item['number']][field] = v
            else:
                parsed['experiment'][k] = v
        return parsed

    def _parse_post(self, data=None):
        """
        create a dictionary containing each of the sub form types.
        """
        parsed = {'experiment': {}, 'authors': [],
                  'dataset': {}, 'file': {}}
        if not data:
            return parsed
        if 'authors' in data:
            parsed['authors'] = [a.strip() for a in
                                 data.get('authors').split(',')]
        for k in data:
            v = data.get(k)
            m = self.re_post_data.match(k)
            if m:
                item = m.groupdict()
                field = item['field']
                if not item['number'] in parsed[item['form']]:
                    parsed[item['form']][item['number']] = {}
                if item['form'] == u'file':
                    v = data.getlist(k)
                    for i in xrange(len(v)):
                        form_list = parsed[item['form']][item['number']]
                        if not form_list:
                            form_list = [{} for v1 in v]
                        form_list[i][field] = v[i]
                        parsed[item['form']][item['number']] = form_list
                else:
                    parsed[item['form']][item['number']][field] = v
            else:
                parsed['experiment'][k] = v
        return parsed

    def _fill_forms(self, data=None, initial=None, instance=None):
        if data and 'authors' in data:
            for num, author in enumerate(data['authors']):
                try:
                    o_author = models.Author.objects.get(name=author)
                except models.Author.DoesNotExist:
                    o_author = None
                f = Author(data={'name': author}, instance=o_author)
                self.authors.append(f)

        self.fields['authors'] = \
            MultiValueCommaSeparatedField([author.fields['name'] for author in self.authors],
                                          widget=CommaSeparatedInput())

        if not data:
            return data

        for number, dataset in data['dataset'].items():

            ds_pk = dataset.get('id')
            try:
                ds_inst = models.Dataset.objects.get(id=ds_pk)
            except models.Dataset.DoesNotExist:
                ds_inst = None
            form = Dataset(data=dataset,
                           instance=ds_inst,
                           auto_id='dataset_%s')
            self._add_dataset_form(number, form)
            self.dataset_files[number] = []

        for number, files in data['file'].items():
            # TODO to cover extra fields we should be looking for all fields
            # starting with file_

            for f in files:
                df_pk = f.get('id')
                try:
                    df_inst = models.Dataset_File.objects.get(id=df_pk)
                except models.Dataset_File.DoesNotExist:
                    df_inst = None

                d = Dataset_File(data=f,
                                 instance=df_inst, auto_id='file_%s')
                self._add_datafile_form(number, d)

        return data

    def _translate_dsfieldname(self, name, number):
        """
        return the dataset forms translated field name
        """
        return self.dataset_field_translation[name] + '[' + str(number) + ']'

    def _add_dataset_form(self, number, form):
        self.datasets[number] = form
        setattr(form, 'postfix', '[%s]' % number)
        self.__ds_num = self.__ds_num + 1

    def _add_datafile_form(self, number, form):
        setattr(form, 'postfix', '[%s]' % number)
        self.dataset_files[number].append(form)

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
        for number, form in self.datasets.items():
            yield (form, self.get_dataset_files(number))

    def save(self, commit=True):
        # remove m2m field before saving
        del self.cleaned_data['authors']

        experiment = super(FullExperiment, self).save()

        authors = []
        author_experiments = []
        datasets = []
        dataset_files = []

        for num, author in enumerate(self.authors):
            o_author = author.save()
            authors.append(o_author)

            f = Author_Experiment({'author': o_author.pk,
                                   'order': num,
                                   'experiment': experiment.pk})
            author = f.save()
            author_experiments.append(author)

        for key, dataset in self.datasets.items():
            dataset.data['experiment'] = experiment.pk
            dataset = Dataset(dataset.data)
            o_dataset = dataset.save()
            datasets.append(o_dataset)
            # save any datafiles if the data set has any
            if key in self.dataset_files:
                for df in self.dataset_files[key]:
                    df.data['dataset'] = o_dataset.pk
                    dataset_file = Dataset_File(df.data)
                    ds = dataset_file.save(commit)
                    dataset_files.append(ds)

        return {'experiment': experiment,
                'author_experiments': author_experiments,
                'authors': authors,
                'datasets': datasets,
                'dataset_files': dataset_files}

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
        for author in self.authors:
            for name, error in author.errors.items():
                if isinstance(author.fields[name], ModelChoiceField):
                    continue
                if author.is_bound and bool(author.errors[name]):
                    return False

        for dataset, files in self.get_datasets():
            for name, error in dataset.errors.items():
                if isinstance(dataset.fields[name], ModelChoiceField):
                    continue
                print dataset.errors[name]
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
            schema__namespace__in=[constants.SCHEMA_DICT[searchQueryType] \
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
    fields['creator'] = forms.CharField(label="Author's Name",
            max_length=20, required=False)

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
    paramChoices = []

    # we'll always add '-' as the default value for a dropdown menu just
    # incase the user doesn't specify a value they'd like to search for
    paramChoices.append(('-', '-'))
    dropDownEntryPattern = re.compile(r'\((.*):(.*)\)')

    dropDownEntryStrings = string.split(choicesString, ',')
    for dropDownEntry in dropDownEntryStrings:
        dropDownEntry = string.strip(dropDownEntry)
        (key, value) = dropDownEntryPattern.search(dropDownEntry).groups()
        paramChoices.append((str(key), str(value)))

    return tuple(paramChoices)


def createSearchDatafileSelectionForm():

    from tardis.tardis_portal import constants

    supportedDatafileSearches = [('-', 'Datafile')]
    for key in constants.SCHEMA_DICT:
        supportedDatafileSearches.append((key, key.upper()))

    fields = {}
    fields['type'] = \
        forms.CharField(label='type',
        widget=forms.Select(choices=tuple(supportedDatafileSearches)),
        required=False)
    fields['type'].widget.attrs['class'] = 'searchdropdown'

    return type('DatafileSelectionForm', (forms.BaseForm, ),
                    {'base_fields': fields})
           
