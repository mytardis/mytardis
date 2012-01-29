# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, RMIT e-Research Office
#   (RMIT University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of RMIT University nor the
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

from django import forms
from tardis.apps.hpctardis.models import ActivityRecord
from tardis.apps.hpctardis.models import PartyRecord

class ActivitiesSelectForm(forms.Form):
    activities = forms.ModelMultipleChoiceField(queryset=ActivityRecord.objects.all())
    
    
class CollectionPartyRelation(forms.Form):    
    relation = forms.ChoiceField(choices=[('hasCollector','hasCollector: has been aggregated by the related party'),
                                          ('isManagedBy','isManagedBy: is maintained and made accessible by the related party (includes custodian role)'),
                                          ('isOwnedBy ','isOwnedBy: legally belongs to the related party'),
                                          ('isEnrichedBy ','isEnrichedBy: additional value provided to a collection by a party')])
    party = forms.ModelChoiceField(required=False,queryset=PartyRecord.objects.all())
  
from tardis.tardis_portal.ParameterSetManager import ParameterSetManager

    
def  create_parameterset_edit_form_alt(
    parameterset,
    request=None):
    """ Override of tardis_portal.forms.create_paramset_edit_form
      which uses TextArea rather than TextInput"""

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
                                        initial=value,
                                        widget=forms.Textarea(attrs={'rows':1,'cols':80}))
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
                                    initial=dfp.string_value,widget=forms.Textarea(attrs={'rows':1,'cols':255}))

            if dfp.name.immutable:
                fields[form_id].widget.attrs['readonly'] = 'readonly'

        return type('DynamicForm', (forms.BaseForm, ),
                    {'base_fields': fields})




def create_datafile_add_form_alt(
    schema, parentObject,
    request=None):
    """ Override of tardis_portal.forms.create_datafile_add_form
      which uses TextArea rather than TextInput"""

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
                                    widget=forms.Textarea(attrs={'rows':1,'cols':255}))
                                    

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
                max_length=255, required=False,
                widget=forms.Textarea(attrs={'rows':1,'cols':255}))

        return type('DynamicForm', (forms.BaseForm, ),
            {'base_fields': fields})



