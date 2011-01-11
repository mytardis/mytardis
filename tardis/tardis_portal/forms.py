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
from UserDict import UserDict

from django import forms
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import ErrorDict, ErrorList
from django.forms.models import ModelChoiceField, model_to_dict
from django.forms.forms import BoundField
from django.forms.formsets import formset_factory

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
        exclude = ('experiment',)


class Dataset(PostfixedForm, forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = models.Dataset
        exclude = ('experiment',)


class Dataset_File(PostfixedForm, forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    url = forms.CharField(required=False)
    filename = forms.CharField(required=False)

    class Meta:
        model = models.Dataset_File
        fields = ('filename', 'url', 'protocol')


class Experiment(forms.ModelForm):
    class Meta:
        model = models.Experiment
        exclude = ('authors', 'handle', 'approved')


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
    base_fields = {}

    def __init__(self, data=None, files=None, auto_id='%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, extra=1):
        self.author_experiments = []
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

        # initialise formsets
        dataset_formset = formset_factory(Dataset, extra=1)
        datafile_formset = formset_factory(Dataset_File, extra=0)

        # fix up experiment form
        post_data = self._parse_post(data)
        self._fill_forms(post_data)

        # fill formsets
        initial_ds, initial_dfs = self._initialise_from_instance(instance)

        self.datasets = dataset_formset(data=data,
                                        initial=initial_ds,
                                        auto_id='id_%s',
                                        prefix="dataset")
        if initial_dfs:
            for i, df in enumerate(initial_dfs):
                self.dataset_files[i] = datafile_formset(data=data,
                                                         initial=df,
                                                         auto_id="id_%s",
                                                         prefix="dataset-%s-datafile" % i)
        else:
            for i, df in enumerate(self.datasets.forms):
                self.dataset_files[i] = datafile_formset(data=data,
                                                         auto_id="id_%s",
                                                         prefix="dataset-%s-datafile" % i)

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
            return [], []
        authors = experiment.author_experiment_set.all()
        self.authors_experiments = [Author_Experiment(instance=a) for a in authors]
        self.initial['authors'] = ', '.join([a.author for a in authors])
        self.fields['authors'] = \
            MultiValueCommaSeparatedField([author.fields['author'] for author in self.author_experiments],
                                          widget=CommaSeparatedInput())
        datasets = []
        datafiles = []
        for i, ds in enumerate(experiment.dataset_set.all()):

            datasets.append(model_to_dict(ds))

            datafile = []
            for file in ds.dataset_file_set.all():
                datafile.append(model_to_dict(file))
            datafiles.append(datafile)
        return datasets, datafiles

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

    def _fill_forms(self, data=None):
        if data and 'authors' in data:
            if self.instance:
                o_author_experiments = \
                    self.instance.author_experiment_set.all()
            else:
                o_author_experiments = []
            for num, author in enumerate(data['authors']):
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
        return

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
            df = formset_factory(Dataset_File, extra=0)
            yield (form, self.get_dataset_files(number))

    def save(self, commit=True):
        # remove m2m field before saving
        del self.cleaned_data['authors']

        experiment = super(FullExperiment, self).save(commit)

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
                for df in self.dataset_files[key].forms:
                    # XXX for some random reason the link between the instance
                    # needs to be reinitialised
                    df.instance.dataset = o_dataset
                    print df.errors
                    o_df = df.save(commit)
                    dataset_files.append(o_df)

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
