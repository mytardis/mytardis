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

"""
forms module

.. moduleauthor::  Gerson Galang <gerson.galang@versi.edu.au>

"""
import logging
import re

from collections import OrderedDict
from collections import UserDict

from django import forms
from django.contrib.sites.shortcuts import get_current_site
from django.forms import ValidationError
from django.forms.utils import ErrorList
from django.forms.models import ModelChoiceField
from django.forms.widgets import HiddenInput
from django.forms import ModelForm
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm

from registration.models import RegistrationProfile

from . import models
from .fields import MultiValueCommaSeparatedField
from .widgets import CommaSeparatedInput
from .models import UserAuthentication, Experiment, License
from .auth.localdb_auth import auth_key as locabdb_auth_key

from .ParameterSetManager import ParameterSetManager

logger = logging.getLogger(__name__)


def getAuthMethodChoices():
    authMethodChoices = ()
    for authMethods in settings.AUTH_PROVIDERS:
        authMethodChoices += ((authMethods[0], authMethods[1]),)
    return authMethodChoices


attrs_dict = {'class': 'form-control'}


class LoginForm(AuthenticationForm):
    # authMethod = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"] = forms.CharField(
            required=True, label="Username", max_length=75
        )


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
        regex=r"^[\w\.]+$",
        max_length=30,
        widget=forms.TextInput(attrs=attrs_dict),
        label=_("Username"),
        error_messages={
            "invalid": _(
                "This value must contain only letters, \
                        numbers and underscores."
            )
        },
    )
    email = forms.EmailField(
        widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)),
        label=_("Email address"),
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password"),
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password (again)"),
    )

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.

        """
        username = "%s" % self.cleaned_data["username"]

        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("A user with that username already exists."))

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("The two password fields didn't match."))

        return self.cleaned_data

    @transaction.atomic
    def save(self, profile_callback=None):
        user = RegistrationProfile.objects.create_inactive_user(
            site=get_current_site(None),
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],
            email=self.cleaned_data["email"],
        )

        authentication = UserAuthentication(
            userProfile=user.userprofile,
            username=self.cleaned_data["username"],
            authenticationMethod=locabdb_auth_key,
        )
        authentication.save()

        return user


class AddUserPermissionsForm(forms.Form):

    entered_user = forms.CharField(label="User", required=False, max_length=100)
    autocomp_user = forms.CharField(
        label="", required=False, max_length=100, widget=forms.HiddenInput
    )
    authMethod = forms.CharField(
        required=True,
        widget=forms.Select(choices=getAuthMethodChoices()),
        label="Authentication Method",
    )
    read = forms.BooleanField(label="Read access", required=False, initial=True)
    read.widget.attrs["class"] = "canRead"
    write = forms.BooleanField(label="Edit access", required=False)
    write.widget.attrs["class"] = "canWrite"
    delete = forms.BooleanField(label="", required=False, widget=forms.HiddenInput)
    delete.widget.attrs["class"] = "canDelete"


class ManageGroupPermissionsForm(forms.Form):

    authMethod = forms.CharField(
        required=True,
        widget=forms.Select(choices=getAuthMethodChoices()),
        label="Authentication Method",
    )
    adduser = forms.CharField(label="User", required=False, max_length=100)
    adduser.widget.attrs["class"] = "usersuggest"
    admin = forms.BooleanField(label="Group Admin", required=False, initial=False)
    admin.widget.attrs["class"] = "isAdmin"


class CreateUserPermissionsForm(RegistrationForm):
    authMethod = forms.CharField(
        required=True,
        widget=forms.Select(
            choices=getAuthMethodChoices(),
            attrs={'class': 'form-select'}
        ),
        label='Authentication Method')


def createLinkedUserAuthenticationForm(authMethods):
    """Create a LinkedUserAuthenticationForm and use the contents of
    authMethods to the list of options in the dropdown menu for
    authenticationMethod.

    """
    _authenticationMethodChoices = ()
    for authMethodKey in authMethods.keys():
        _authenticationMethodChoices += ((authMethodKey, authMethods[authMethodKey]),)

    fields = {}
    fields["authenticationMethod"] = forms.CharField(
        label="Authentication Method",
        widget=forms.Select(choices=_authenticationMethodChoices),
        required=True,
    )
    fields["username"] = forms.CharField(label="Username", max_length=75, required=True)
    fields["password"] = forms.CharField(
        required=True, widget=forms.PasswordInput(), label="Password"
    )

    return type(
        "LinkedUserAuthenticationForm", (forms.BaseForm,), {"base_fields": fields}
    )


class ImportParamsForm(forms.Form):

    username = forms.CharField(max_length=400, required=True)
    password = forms.CharField(max_length=400, required=True)
    params = forms.FileField()


class RegisterExperimentForm(forms.Form):

    username = forms.CharField(max_length=400, required=True)
    password = forms.CharField(max_length=400, required=True)
    xmldata = forms.FileField(required=False)
    xml_filename = forms.CharField(max_length=400, required=False)
    experiment_owner = forms.CharField(max_length=400, required=False)
    originid = forms.CharField(max_length=400, required=False)
    from_url = forms.CharField(max_length=400, required=False)


class DatasetForm(forms.ModelForm):

    description = forms.CharField()

    class Meta:
        model = models.Dataset
        fields = [
            "description",
            "directory",
            "instrument",
        ]


class ExperimentAuthor(forms.ModelForm):
    class Meta:
        model = models.ExperimentAuthor
        fields = [
            "author",
            "institution",
            "email",
            "order",
            "url",
        ]


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
        fields = ("title", "institution_name", "description")

    class FullExperiment(UserDict):
        """
        This is a dict wrapper that store the values returned from
        the :func:`tardis.tardis_portal.forms.ExperimentForm.save` function.
        It provides a convience method for saving the model objects.
        """

        def save_m2m(self):
            """
            {'experiment': experiment,
            'experiment_authors': experiment_authors,
            'authors': authors,
            'datasets': datasets,
            'datafiles': datafiles}
            """
            self.data["experiment"].save()
            for ae in self.data["experiment_authors"]:
                ae.experiment = self.data["experiment"]
                ae.save()

    def __init__(
        self,
        data=None,
        files=None,
        auto_id="%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=":",
        empty_permitted=False,
        instance=None,
        extra=0,
    ):

        super().__init__(
            data=data,
            files=files,
            auto_id=auto_id,
            prefix=prefix,
            initial=initial,
            instance=instance,
            error_class=error_class,
            label_suffix=label_suffix,
            empty_permitted=False,
        )

        # fix up experiment form
        if instance and not data:
            authors = instance.experimentauthor_set.all()
            self.initial["authors"] = ", ".join(
                [self._format_author(a) for a in authors]
            )

        self.experiment_authors = []

        if data:
            self._update_authors(data)

        self.fields["authors"] = MultiValueCommaSeparatedField(
            [author.fields["author"] for author in self.experiment_authors],
            widget=CommaSeparatedInput(
                attrs={
                    "placeholder": "eg. Howard W. Florey, Brian Schmidt "
                    + "(http://nla.gov.au/nla.party-1480342)"
                }
            ),
            help_text="Comma-separated authors and optional emails/URLs",
        )

    def _format_author(self, author):
        if author.email or author.url:
            author_contacts = [author.email, author.url]
            return "%s (%s)" % (
                author.author,
                ", ".join([c for c in author_contacts if c]),
            )
        return author.author

    def _parse_authors(self, data):
        """
        create a dictionary containing each of the sub form types.
        """
        if "authors" not in data:
            return []

        def build_dict(order, author_str):
            author_str = author_str.strip()
            res = {"order": order}
            # check for email (contains @ sign and one dot after)
            email_match = re.match("([^\(]+)\(([^@]+@[^@]+\.[^@]+)\)", author_str)
            if email_match:
                try:
                    author_str, email = email_match.group(1, 2)
                    # Check that it really is a URL
                    email = ExperimentAuthor().fields["email"].clean(email)
                    res["email"] = email
                except ValidationError:
                    pass
            # check for url (any non zero string)
            url_match = re.match("([^\(]+)\(([^\)]+)\)", author_str)
            if url_match:
                try:
                    author_str, url = url_match.group(1, 2)
                    # Check that it really is a URL
                    url = ExperimentAuthor().fields["url"].clean(url)
                    res["url"] = url
                except ValidationError:
                    pass
            res["author"] = author_str.strip()
            return res

        return [build_dict(i, a) for i, a in enumerate(data.get("authors").split(","))]

    def _update_authors(self, data):
        # For each author in the POST in a position
        for author_data in self._parse_authors(data):
            try:
                # Get the current author for that position
                o_ae = self.experiment_authors[author_data["order"]]
                # Update the author form for that position with the new author_data
                self.experiment_authors[author_data["order"]] = ExperimentAuthor(
                    data=author_data, instance=o_ae.instance
                )
            except IndexError:
                # Or create an author for that position
                o_ae = ExperimentAuthor(
                    data=author_data, instance=models.ExperimentAuthor()
                )
                self.experiment_authors.append(o_ae)

    def save(self, commit=True):
        # remove m2m field before saving
        del self.cleaned_data["authors"]

        # fix up experiment form
        if self.instance:
            authors = self.instance.experimentauthor_set.all()
            for author in authors:
                author.delete()

        experiment = super().save(commit)

        authors = []
        experiment_authors = []

        for ae in self.experiment_authors:
            o_ae = ae.save(commit=commit)
            experiment_authors.append(o_ae)

        return self.FullExperiment(
            {
                "experiment": experiment,
                "experiment_authors": experiment_authors,
                "authors": authors,
            }
        )

    def is_valid(self):
        """
        Test the validity of the form, the form may be invalid even if the
        error attribute has no contents. This is because the returnd value
        is dependent on the validity of the nested forms.

        This validity also takes into account forign keys that might be
        dependent on an unsaved model.

        :return: validity
        :rtype: bool
        """
        if self.is_bound and bool(self.errors):
            return not bool(self.errors)

        # TODO since this is a compound field, this should merge the errors
        for ae in self.experiment_authors:
            for name, _ in ae.errors.items():
                if isinstance(ae.fields[name], ModelChoiceField):
                    continue
                if ae.is_bound and bool(ae.errors[name]):
                    return False
        return True


def __getParameterChoices(choicesString):
    """Handle the choices string in this format:
    '(hello:hi how are you), (yes:i am here), (no:joe)'

    Note that this parser is very strict and is not smart enough to handle
    any extra unknown characters that the user might put in the choices
    textbox.

    """
    paramChoices = ()

    # we'll always add '-' as the default value for a dropdown menu just
    # incase the user doesn't specify a value they'd like to search for
    paramChoices += (("-", "-"),)
    dropDownEntryPattern = re.compile(r"\((.*):(.*)\)")

    dropDownEntryStrings = choicesString.split(",")
    for dropDownEntry in dropDownEntryStrings:
        dropDownEntry = dropDownEntry.strip()
        (key, value) = dropDownEntryPattern.search(dropDownEntry).groups()
        paramChoices += ((str(key), str(value)),)

    return paramChoices


class NoInput(forms.Widget):
    def render(self, name, value, attrs=None):
        from django.utils.safestring import mark_safe

        return mark_safe(value)


class StaticField(forms.Field):

    widget = NoInput

    def clean(self, value):
        return


def create_parameterset_edit_form(
    parameterset, request, post=False, view_sensitive=False
):

    from .models import ParameterName

    # if POST data to save
    if post:
        fields = OrderedDict()

        for key, value in sorted(request.POST.items()):

            x = 1
            stripped_key = key.replace("_s47_", "/")
            stripped_key = stripped_key.rpartition("__")[0]

            parameter_name = ParameterName.objects.get(
                schema=parameterset.schema, name=stripped_key
            )

            units = ""
            if parameter_name.units:
                units = " (" + parameter_name.units + ")"
                # if not valid, spit back as exact
                if parameter_name.isNumeric():
                    fields[key] = forms.DecimalField(
                        label=parameter_name.full_name + units,
                        required=False,
                        initial=value,
                    )
                elif parameter_name.isLongString():
                    fields[key] = forms.CharField(
                        widget=forms.Textarea,
                        label=parameter_name.full_name + units,
                        max_length=255,
                        required=False,
                        initial=value,
                    )
                else:
                    fields[key] = forms.CharField(
                        label=parameter_name.full_name + units,
                        max_length=255,
                        required=False,
                        initial=value,
                    )

        return type("DynamicForm", (forms.BaseForm,), {"base_fields": fields})

    fields = OrderedDict()
    psm = ParameterSetManager(parameterset=parameterset)

    for dfp in psm.parameters:
        if dfp.name.sensitive:
            if not view_sensitive:
                continue

        x = 1
        form_id = dfp.name.name + "__" + str(x)

        while form_id in fields:
            x = x + 1
            form_id = dfp.name.name + "__" + str(x)

        units = ""
        if dfp.name.units:
            units = " (" + dfp.name.units + ")"

        form_id = form_id.replace("/", "_s47_")
        if dfp.name.isNumeric():
            fields[form_id] = forms.DecimalField(
                label=dfp.name.full_name + units,
                required=False,
                initial=dfp.numerical_value,
            )
        elif dfp.name.isLongString():
            fields[form_id] = forms.CharField(
                widget=forms.Textarea,
                label=dfp.name.full_name + units,
                max_length=255,
                required=False,
                initial=dfp.string_value,
            )

        else:
            fields[form_id] = forms.CharField(
                label=dfp.name.full_name + units,
                max_length=255,
                required=False,
                initial=dfp.string_value,
            )

        if dfp.name.immutable or dfp.name.schema.immutable:
            fields[form_id].widget.attrs["readonly"] = True
            fields[form_id].label = fields[form_id].label + " (read only)"

        if dfp.name.sensitive:
            fields[form_id].widget.attrs["readonly"] = True
            fields[form_id].label = (
                fields[form_id].label + " (Sensitive: cannot be edited)"
            )

    return type("DynamicForm", (forms.BaseForm,), {"base_fields": fields})


def save_parameter_edit_form(parameterset, request, view_sensitive=False):

    psm = ParameterSetManager(parameterset=parameterset)
    # psm.delete_all_params()

    for key, value in sorted(request.POST.items()):
        stripped_key = key.replace("_s47_", "/")
        stripped_key = stripped_key.rpartition("__")[0]

        if psm.get_param_sens_flag(stripped_key) and not view_sensitive:
            continue
        if value:
            psm.set_param(stripped_key, value)
        else:
            psm.get_param(stripped_key).delete()

    psm = ParameterSetManager(parameterset=parameterset)
    if not psm.parameters.exists():
        parameterset.delete()


def create_parameter_add_form(schema, parentObject, request=None):

    from .models import ParameterName

    # if POST data to save
    if request:
        fields = OrderedDict()

        for key, value in sorted(request.POST.items()):

            x = 1

            stripped_key = key.replace("_s47_", "/")
            stripped_key = stripped_key.rpartition("__")[0]

            parameter_name = ParameterName.objects.get(
                schema__namespace=schema, name=stripped_key
            )

            if parameter_name.immutable is False:
                units = ""
                if parameter_name.units:
                    units = " (" + parameter_name.units + ")"

                # if not valid, spit back as exact
                if parameter_name.isNumeric():
                    fields[key] = forms.DecimalField(
                        label=parameter_name.full_name + units,
                        required=False,
                        initial=value,
                    )
                elif parameter_name.isLongString():
                    fields[key] = forms.CharField(
                        widget=forms.Textarea,
                        label=parameter_name.full_name + units,
                        max_length=255,
                        required=False,
                        initial=value,
                    )
                elif parameter_name.isDateTime():
                    fields[key] = forms.DateTimeField(
                        label=parameter_name.full_name + units,
                        required=False,
                        initial=value,
                    )
                else:
                    fields[key] = forms.CharField(
                        label=parameter_name.full_name + units,
                        max_length=255,
                        required=False,
                        initial=value,
                    )

        return type("DynamicForm", (forms.BaseForm,), {"base_fields": fields})

    fields = OrderedDict()

    parameternames = ParameterName.objects.filter(
        schema__namespace=schema, immutable=False
    ).order_by("name")

    for dfp in parameternames:

        x = 1

        form_id = dfp.name + "__" + str(x)

        while form_id in fields:
            x = x + 1
            form_id = dfp.name + "__" + str(x)

        units = ""
        if dfp.units:
            units = " (" + dfp.units + ")"

        form_id = form_id.replace("/", "_s47_")

        if dfp.isNumeric():
            fields[form_id] = forms.DecimalField(
                label=dfp.full_name + units, required=False
            )
        elif dfp.isLongString():
            fields[form_id] = forms.CharField(
                label=dfp.full_name + units,
                widget=forms.Textarea,
                required=False,
                max_length=255,
            )
        else:
            fields[form_id] = forms.CharField(
                label=dfp.full_name + units, max_length=255, required=False
            )

    return type("DynamicForm", (forms.BaseForm,), {"base_fields": fields})


def save_parameter_add_form(schema, parentObject, request):

    psm = ParameterSetManager(schema=schema, parentObject=parentObject)

    for key, value in sorted(request.POST.items()):
        if value:
            stripped_key = key.replace("_s47_", "/")
            stripped_key = stripped_key.rpartition("__")[0]

            psm.new_param(stripped_key, value)


class RightsForm(ModelForm):
    """
    Form for changing public access and licence.

    """

    legal_text = forms.CharField(label="Legal Text", widget=forms.HiddenInput())

    class Meta:
        model = Experiment
        fields = ("public_access", "license", "legal_text")
        widgets = {"license": HiddenInput()}

    def clean(self):
        cleaned_data = super().clean()
        public_access = cleaned_data.get("public_access")
        license_ = cleaned_data.get("license")

        if license_ is None:
            # Only data which is not distributed can have no explicit licence
            suitable = not Experiment.public_access_implies_distribution(public_access)
        else:
            suitable = license_ in License.get_suitable_licenses(public_access)

        if not suitable:
            raise forms.ValidationError(
                "Selected license it not suitable " + "for public access level."
            )

        return cleaned_data


class ManageAccountForm(ModelForm):
    """
    Form for changing account details.

    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
