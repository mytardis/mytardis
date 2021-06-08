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
test_parametersets.py
http://docs.djangoproject.com/en/dev/topics/testing/

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  Steve Androulakis <steve.androulakis@monash.edu>

"""

from datetime import datetime

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
import pytz

from ..models.experiment import Experiment
from ..models.dataset import Dataset
from ..models.datafile import DataFile, DataFileObject
from ..models.parameters import (Schema, ParameterName, DatafileParameterSet,
                                 DatafileParameter, DatasetParameterSet,
                                 ExperimentParameterSet, ExperimentParameter)
from ..models.access_control import ExperimentACL
from ..ParameterSetManager import ParameterSetManager
from ..views.parameters import edit_datafile_par
from ..views.parameters import edit_dataset_par
from ..views.parameters import edit_experiment_par
from ..views.parameters import add_datafile_par
from ..views.parameters import add_dataset_par
from ..views.parameters import add_experiment_par


class ParameterSetManagerTestCase(TestCase):

    def setUp(self):
        from tempfile import mkdtemp

        user = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(user, email, pwd)

        self.test_dir = mkdtemp()

        self.exp = Experiment(title='test exp1',
                              institution_name='monash',
                              created_by=self.user)
        self.exp.save()

        self.dataset = Dataset(description="dataset description...")
        self.dataset.save()
        self.dataset.experiments.add(self.exp)
        self.dataset.save()

        self.datafile = DataFile(dataset=self.dataset,
                                 filename="testfile.txt",
                                 size="42", md5sum='bogus')
        self.datafile.save()

        self.dfo = DataFileObject(
            datafile=self.datafile,
            storage_box=self.datafile.get_default_storage_box(),
            uri="1/testfile.txt")
        self.dfo.save()

        self.schema = Schema(
            namespace="http://localhost/psmtest/df/",
            name="Parameter Set Manager", type=Schema.DATAFILE)
        self.schema.save()

        self.parametername1 = ParameterName(
            schema=self.schema, name="parameter1",
            full_name="Parameter 1")
        self.parametername1.save()

        self.parametername2 = ParameterName(
            schema=self.schema, name="parameter2",
            full_name="Parameter 2",
            data_type=ParameterName.NUMERIC)
        self.parametername2.save()

        self.parametername3 = ParameterName(
            schema=self.schema, name="parameter3",
            full_name="Parameter 3",
            data_type=ParameterName.DATETIME)
        self.parametername3.save()

        self.datafileparameterset = DatafileParameterSet(
            schema=self.schema, datafile=self.datafile)
        self.datafileparameterset.save()

        self.datafileparameter1 = DatafileParameter(
            parameterset=self.datafileparameterset,
            name=self.parametername1, string_value="test1")
        self.datafileparameter1.save()

        self.datafileparameter2 = DatafileParameter(
            parameterset=self.datafileparameterset,
            name=self.parametername2, numerical_value=2)
        self.datafileparameter2.save()

        # Create a ParameterName and Parameter of type LINK to an experiment
        self.parametername_exp_link = ParameterName(
            schema=self.schema, name="exp_link",
            full_name="This parameter is a experiment LINK",
            data_type=ParameterName.LINK)
        self.parametername_exp_link.save()

        self.exp_link_param = DatafileParameter(
            parameterset=self.datafileparameterset,
            name=self.parametername_exp_link)
        exp_url = self.exp.get_absolute_url()  # /experiment/view/1/
        self.exp_link_param.set_value(exp_url)
        self.exp_link_param.save()

        # Create a ParameterName and Parameter of type LINK to a dataset
        self.parametername_dataset_link = ParameterName(
            schema=self.schema, name="dataset_link",
            full_name="This parameter is a dataset LINK",
            data_type=ParameterName.LINK)
        self.parametername_dataset_link.save()

        self.dataset_link_param = DatafileParameter(
            parameterset=self.datafileparameterset,
            name=self.parametername_dataset_link)
        dataset_url = self.dataset.get_absolute_url()  # /dataset/1/
        self.dataset_link_param.set_value(dataset_url)
        self.dataset_link_param.save()

        # Create a ParameterName type LINK to an unresolvable (non-URL)
        # free-text value
        self.parametername_unresolvable_link = ParameterName(
                schema=self.schema, name="freetext_link",
                full_name="This parameter is a non-URL LINK",
                data_type=ParameterName.LINK)
        self.parametername_unresolvable_link.save()

    def tearDown(self):
        self.exp.delete()
        self.user.delete()
        self.parametername1.delete()
        self.parametername2.delete()
        self.parametername3.delete()
        self.parametername_exp_link.delete()
        self.parametername_dataset_link.delete()
        self.parametername_unresolvable_link.delete()
        self.schema.delete()

    def test_parameterset_as_string(self):
        self.assertEqual(
            str(self.datafileparameterset),
            "%s / %s" % (self.schema.namespace, self.datafile.filename))

    def test_existing_parameterset(self):

        psm = ParameterSetManager(parameterset=self.datafileparameterset)

        self.assertTrue(psm.get_schema().namespace ==
                        "http://localhost/psmtest/df/")

        self.assertTrue(psm.get_param("parameter1").string_value == "test1")

        self.assertTrue(psm.get_param("parameter2", True) == 2)

    def test_new_parameterset(self):

        psm = ParameterSetManager(parentObject=self.datafile,
                                  schema="http://localhost/psmtest/df2/")

        self.assertTrue(psm.get_schema().namespace ==
                        "http://localhost/psmtest/df2/")

        psm.set_param("newparam1", "test3", "New Parameter 1")

        self.assertTrue(psm.get_param("newparam1").string_value ==
                        "test3")

        self.assertTrue(psm.get_param("newparam1").name.full_name ==
                        "New Parameter 1")

        psm.new_param("newparam1", "test4")

        self.assertTrue(len(psm.get_params("newparam1", True)) == 2)

        psm.set_param_list("newparam2", ("a", "b", "c", "d"))

        self.assertTrue(len(psm.get_params("newparam2")) == 4)

        psm.set_params_from_dict(
            {"newparam2": "test5", "newparam3": 3})

        self.assertTrue(psm.get_param("newparam2", True) == "test5")

        # the newparam3 gets created and '3' is set to a string_value
        # since once cannot assume that an initial numeric value
        # will imply continuing numeric type for this new param
        self.assertTrue(psm.get_param("newparam3").string_value == '3')

        psm.delete_params("newparam1")

        self.assertTrue(len(psm.get_params("newparam1", True)) == 0)

    def test_link_parameter_type(self):
        """
        Test that Parameter.link_gfk (GenericForeignKey) is correctly
        assigned after using Parameter.set_value(some_url) for a LINK Parameter.
        """
        psm = ParameterSetManager(parameterset=self.datafileparameterset)

        # Check link to experiment
        exp_url = self.exp.get_absolute_url()  # /experiment/view/1/
        self.assertTrue(psm.get_param("exp_link").string_value ==
                        exp_url)

        self.assertTrue(psm.get_param("exp_link").link_id ==
                        self.exp.id)

        exp_ct = ContentType.objects.get(model__iexact="experiment")
        self.assertTrue(psm.get_param("exp_link").link_ct == exp_ct)

        self.assertTrue(psm.get_param("exp_link").link_gfk == self.exp)

        # Check link to dataset
        dataset_url = self.dataset.get_absolute_url()  # /dataset/1/
        self.assertTrue(psm.get_param("dataset_link").string_value ==
                        dataset_url)

        self.assertTrue(psm.get_param("dataset_link").link_id ==
                        self.dataset.id)

        dataset_ct = ContentType.objects.get(model__iexact="dataset")
        self.assertTrue(psm.get_param("dataset_link").link_ct == dataset_ct)

        self.assertTrue(psm.get_param("dataset_link").link_gfk == self.dataset)

    def test_link_parameter_type_extra(self):
        # make a second ParameterSet for testing some variations
        # in URL values
        self.datafileparameterset2 = DatafileParameterSet(
            schema=self.schema, datafile=self.datafile)
        self.datafileparameterset2.save()

        psm = ParameterSetManager(parameterset=self.datafileparameterset2)

        self.dataset_link_param2 = DatafileParameter(
            parameterset=self.datafileparameterset2,
            name=self.parametername_dataset_link)
        # /dataset/1 - no trailing slash
        dataset_url = self.dataset.get_absolute_url()
        self.dataset_link_param2.set_value(dataset_url)
        self.dataset_link_param2.save()

        # Check link_id/link_ct/link_gfk to dataset
        self.assertTrue(psm.get_param("dataset_link").link_id ==
                        self.dataset.id)

        dataset_ct = ContentType.objects.get(model__iexact="dataset")
        self.assertTrue(psm.get_param("dataset_link").link_ct == dataset_ct)

        self.assertTrue(psm.get_param("dataset_link").link_gfk == self.dataset)

        # Test links of the form /api/v1/experiment/<experiment_id>/
        self.exp_link_param2 = DatafileParameter(
            parameterset=self.datafileparameterset2,
            name=self.parametername_exp_link)
        exp_url = '/api/v1/experiment/%s/' % self.exp.id
        self.exp_link_param2.set_value(exp_url)
        self.exp_link_param2.save()

        # Check link_id/link_ct/link_gfk to experiment
        self.assertTrue(psm.get_param("exp_link").link_id ==
                        self.exp.id)

        exp_ct = ContentType.objects.get(model__iexact="experiment")
        self.assertTrue(psm.get_param("exp_link").link_ct == exp_ct)

        self.assertTrue(psm.get_param("exp_link").link_gfk == self.exp)

    def test_unresolvable_link_parameter(self):
        """
        Test that LINK Parameters that can't be resolved to a model (including
        non-URL values) still work.
        """
        self.datafileparameterset3 = DatafileParameterSet(
                schema=self.schema, datafile=self.datafile)
        self.datafileparameterset3.save()

        # Create a Parameter of type LINK to an unresolvable (non-URL)
        # free-text value
        self.freetext_link_param = DatafileParameter(
                parameterset=self.datafileparameterset3,
                name=self.parametername_unresolvable_link)
        self.assertRaises(SuspiciousOperation,
                          lambda: self.freetext_link_param.set_value(
                              "FREETEXT_ID_123"))

    def test_tz_naive_date_handling(self):
        """
        Ensure that dates are handling in a timezone-aware way.
        """
        psm = ParameterSetManager(parameterset=self.datafileparameterset)

        psm.new_param("parameter3", str(datetime(1970, 1, 1, 10, 0, 0)))

        self.assertEqual(
            psm.get_param("parameter3", True),
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc))

    def test_tz_aware_date_handling(self):
        """
        Ensure that dates are handling in a timezone-aware way.
        """
        psm = ParameterSetManager(parameterset=self.datafileparameterset)

        psm.new_param("parameter3",
                      '1970-01-01T08:00:00+08:00')

        self.assertEqual(
            psm.get_param("parameter3", True),
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc))


class EditParameterSetTestCase(TestCase):
    def setUp(self):
        username = 'tardis_user1'
        pwd = 'secret'  # nosec
        email = ''
        self.user = User.objects.create_user(username, email, pwd)
        self.user.user_permissions.add(
            Permission.objects.get(codename='change_experiment'))

        self.schema = Schema(
            namespace="http://localhost/psmtest/df/",
            name="Parameter Set Manager", type=Schema.DATAFILE)
        self.schema.save()

        self.parametername1 = ParameterName(
            schema=self.schema, name="parameter1",
            full_name="Parameter 1",
            units="units1")
        self.parametername1.save()

        self.parametername2 = ParameterName(
            schema=self.schema, name="parameter2",
            full_name="Parameter 2",
            data_type=ParameterName.NUMERIC,
            units="items")
        self.parametername2.save()

        self.parametername3 = ParameterName(
            schema=self.schema, name="parameter3",
            full_name="Parameter 3",
            data_type=ParameterName.DATETIME)
        self.parametername3.save()

        self.experiment = Experiment(
            title='test exp1', institution_name='monash', created_by=self.user)
        self.experiment.save()

        self.dataset = Dataset(description='test dataset1')
        self.dataset.save()
        self.dataset.experiments.add(self.experiment)
        self.dataset.save()

        self.acl = ExperimentACL(
            user=self.user,
            experiment=self.experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ExperimentACL.OWNER_OWNED)
        self.acl.save()

        self.experimentparameterset = ExperimentParameterSet(
            schema=self.schema, experiment=self.experiment)
        self.experimentparameterset.save()

        self.exp_param1 = ExperimentParameter.objects.create(
            parameterset=self.experimentparameterset,
            name=self.parametername1, string_value="value1")

        self.exp_param2 = ExperimentParameter.objects.create(
            parameterset=self.experimentparameterset,
            name=self.parametername2, numerical_value=987)

        self.exp_param3 = ExperimentParameter.objects.create(
            parameterset=self.experimentparameterset,
            name=self.parametername3, datetime_value=timezone.now())

        self.datasetparameterset = DatasetParameterSet(
            schema=self.schema, dataset=self.dataset)
        self.datasetparameterset.save()

        self.datafile = DataFile(dataset=self.dataset,
                                 filename="testfile.txt",
                                 size="42", md5sum='bogus')
        self.datafile.save()

        self.datafileparameterset = DatafileParameterSet(
            schema=self.schema, datafile=self.datafile)
        self.datafileparameterset.save()

    def test_edit_experiment_params(self):
        factory = RequestFactory()

        request = factory.get(
            '/ajax/edit_experiment_parameters/%s/'
            % self.experimentparameterset.id)
        request.user = self.user
        response = edit_experiment_par(request, self.experimentparameterset.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            '/ajax/edit_experiment_parameters/%s/'
            % self.experimentparameterset.id,
            data={
                'csrfmiddlewaretoken': 'bogus',
                'parameter1__1': 'parameter1 value',
                'parameter2__2': 123
            })
        request.user = self.user
        response = edit_experiment_par(request, self.experimentparameterset.id)
        self.assertEqual(response.status_code, 200)

    def test_add_experiment_params(self):
        factory = RequestFactory()

        request = factory.get(
            '/ajax/add_experiment_parameters/%s/'
            % self.experiment.id)
        request.user = self.user
        response = add_experiment_par(request, self.experiment.id)
        self.assertEqual(response.status_code, 200)

        request = factory.get(
            '/ajax/add_experiment_parameters/%s/?schema_id=%s'
            % (self.experiment.id, self.schema.id))
        request.user = self.user
        response = add_experiment_par(request, self.experiment.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            '/ajax/add_experiment_parameters/%s/?schema_id=%s'
            % (self.experiment.id, self.schema.id),
            data={'csrfmiddlewaretoken': 'bogus'})
        request.user = self.user
        response = add_experiment_par(request, self.experiment.id)
        self.assertEqual(response.status_code, 200)

    def test_edit_dataset_params(self):
        factory = RequestFactory()

        request = factory.get(
            '/ajax/edit_dataset_parameters/%s/'
            % self.datasetparameterset.id)
        request.user = self.user
        response = edit_dataset_par(request, self.datasetparameterset.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            '/ajax/edit_dataset_parameters/%s/'
            % self.datasetparameterset.id,
            data={'csrfmiddlewaretoken': 'bogus'})
        request.user = self.user
        response = edit_dataset_par(request, self.datasetparameterset.id)
        self.assertEqual(response.status_code, 200)

    def test_add_dataset_params(self):
        factory = RequestFactory()

        request = factory.get(
            '/ajax/add_dataset_parameters/%s/'
            % self.dataset.id)
        request.user = self.user
        response = add_dataset_par(request, self.dataset.id)
        self.assertEqual(response.status_code, 200)

        request = factory.get(
            '/ajax/add_dataset_parameters/%s/?schema_id=%s'
            % (self.dataset.id, self.schema.id))
        request.user = self.user
        response = add_dataset_par(request, self.dataset.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            '/ajax/add_dataset_parameters/%s/?schema_id=%s'
            % (self.dataset.id, self.schema.id),
            data={'csrfmiddlewaretoken': 'bogus'})
        request.user = self.user
        response = add_dataset_par(request, self.dataset.id)
        self.assertEqual(response.status_code, 200)

    def test_edit_datafile_params(self):
        factory = RequestFactory()

        request = factory.get(
            '/ajax/edit_datafile_parameters/%s/'
            % self.datafileparameterset.id)
        request.user = self.user
        response = edit_datafile_par(request, self.datafileparameterset.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            '/ajax/edit_datafile_parameters/%s/'
            % self.datafileparameterset.id,
            data={'csrfmiddlewaretoken': 'bogus'})
        request.user = self.user
        response = edit_datafile_par(request, self.datafileparameterset.id)
        self.assertEqual(response.status_code, 200)

    def test_add_datafile_params(self):
        factory = RequestFactory()

        request = factory.get(
            '/ajax/add_datafile_parameters/%s/'
            % self.datafile.id)
        request.user = self.user
        response = add_datafile_par(request, self.datafile.id)
        self.assertEqual(response.status_code, 200)

        request = factory.get(
            '/ajax/add_datafile_parameters/%s/?schema_id=%s'
            % (self.datafile.id, self.schema.id))
        request.user = self.user
        response = add_datafile_par(request, self.datafile.id)
        self.assertEqual(response.status_code, 200)

        request = factory.post(
            '/ajax/add_datafile_parameters/%s/?schema_id=%s'
            % (self.datafile.id, self.schema.id),
            data={'csrfmiddlewaretoken': 'bogus'})
        request.user = self.user
        response = add_datafile_par(request, self.datafile.id)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.experiment.delete()
        self.dataset.delete()
        self.user.delete()
        self.schema.delete()
