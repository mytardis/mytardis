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

from django import forms
from django.forms.util import ErrorDict
from django.forms.models import ModelChoiceField
from django.forms.fields import MultiValueField

from tardis.tardis_portal import models
from tardis.tardis_portal.fields import MultiValueCommaSeparatedField


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


class Author_Experiment(forms.ModelForm):
    class Meta:
        model = models.Author_Experiment


class Author(forms.ModelForm):
    class Meta:
        model = models.Author


class Dataset(forms.ModelForm):
    class Meta:
        model = models.Dataset


class Dataset_File(forms.ModelForm):
    class Meta:
        model = models.Dataset_File


class Experiment(forms.ModelForm):
    class Meta:
        model = models.Experiment
        exclude = ('authors',)


class FullExperiment(forms.BaseForm):
    """
    This handles the complex experiemnt forms.

    The post format is expected to be like::

        abstract Test
        authors Mr Bob
        dataset_description[0] 1
        dataset_description[2] 2
        dataset_description[3] 3
        file[0] 2R9Y/downloadFiles.py
        file[0] 2R9Y/Images/0510060001.osc
        file[0] 2R9Y/Images/0510060002.osc
        file[0] 2R9Y/Images/0510060003.osc
        file[0] 2R9Y/Images/0510060004.osc
        file[0] 2R9Y/Images/0510060005.osc
        file[0] 2R9Y/Images/0510060006.osc
        file[0] 2R9Y/Images/0510060007.osc
        file[0] 2R9Y/Images/0510060008.osc
        file[0] 2R9Y/Images/0510060009.osc
        file[0] 2R9Y/Images/0510060010.osc
        file[0] 2R9Y/Images/traverseScript/traverse.py
        file[0] 2R9Y/toplevel.log
        file[2] 2R9Y/downloadFiles.py
        file[3] 2R9Y/downloadFiles.py
        file[3] 2R9Y/toplevel.log
        title Test Title

    """
    re_dataset = re.compile('dataset_description\[([\d]+)\]$')
    dataset_field_translation = {"description": "dataset_description"}
    base_fields = {}

    def __init__(self, data=None, initial=None):
        super(FullExperiment, self).__init__(data=data, initial=initial)

        self.experiment = None
        self.authors = []
        self.datasets = {}
        self.data_files = {}
        self.fields = {}
        if data:
            self.parsed_data = self.parse_form(data)

    def parse_form(self, data):
        experiment = Experiment(data)
        self.experiment = experiment
        self.fields.update(self.experiment.fields)

        authors = [(c, a.strip()) for c, a in
                   enumerate(data.get('authors').split(','))]
        for num, author in authors:
            f = Author({'name': author})
            self.authors.append(f)
        self.fields['authors'] = MultiValueCommaSeparatedField(self.authors)

        for k, v in data.items():
            match = self.re_dataset.match(k)
            if not match:
                continue
            number = match.groups()[0]
            form = Dataset({'description': v})
            self._add_dataset_form(number, form)

            self.data_files[number] = []

            datafiles = data.getlist('file[' + number + ']')

            for f in datafiles:
                d = Dataset_File({'filename': f})
                self._add_datafile_form(number, d)

        return data

    def _translate_dsfieldname(self, name, number):
        """
        return the dataset forms translated field name
        """
        return self.dataset_field_translation[name] + '[' + str(number) + ']'

    def _add_dataset_form(self, number, form):
        self.datasets[number] = form
        for name, field in self.datasets[number].fields.items():
            if isinstance(field, ModelChoiceField):
                continue
            self.fields[self._translate_dsfieldname(name, number)] = field

    def _add_datafile_form(self, number, form):
        self.data_files[number].append(form)
        self.fields['files[' + number + ']'] = \
            MultiValueField(self.data_files[number])

    def _get_errors(self):
        errors = ErrorDict()
        errors.update(self.experiment.errors)

        # TODO since this is a compound field, this should merge the errors
        for author in self.authors:
            errors.update(author.errors)

        for number, dataset in self.datasets.items():
            for name, error in dataset.errors.items():
                if isinstance(dataset.fields[name], ModelChoiceField):
                    continue
                errors[self._translate_dsfieldname(name, number)] = \
                    dataset.errors[name]

        return errors

    errors = property(_get_errors)

    def save(self):
        experiment = self.experiment.save()
        for num, author in enumerate(self.authors):
            try:
                o_author = models.Author.objects.get(name=author.data['name'])
            except models.Author.DoesNotExist:
                o_author = author.save()

            f = Author_Experiment({'author': o_author.pk,
                                   'order': num,
                                   'experiment': experiment.pk})
            author = f.save()

        for key, dataset in self.datasets.items():
            dataset.data['experiment'] = experiment.pk
            dataset = Dataset(dataset.data)
            o_dataset = dataset.save()
            # save any datafiles if the data set has any
            if key in self.data_files:
                for df in self.data_files[key]:
                    df.data['dataset'] = o_dataset.pk
                    dataset_file = Dataset_File(df.data)
                    print dataset_file.errors
                    dataset_file.save()

        return experiment

    def is_valid(self):
        return not bool(self.errors)


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
