# -*- coding: utf-8 -*-
"""
test_parameters.py

.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

import pytz

from ..models.datafile import DataFile
from ..models.dataset import Dataset
from ..models.experiment import Experiment
from ..models.parameters import (
    DatafileParameter,
    DatafileParameterSet,
    DatasetParameter,
    DatasetParameterSet,
    ExperimentParameter,
    ExperimentParameterSet,
    ParameterName,
    Schema,
)


class ParametersTestCase(TestCase):
    """
    Tests for the different parameter types, defined in the
    tardis.tardis_portal.models.parameters.ParameterName class:

    NUMERIC, STRING, URL, LINK, FILENAME, DATETIME, LONGSTRING and JSON
    """

    def setUp(self):
        user = "tardis_user1"
        pwd = "secret"  # nosec
        email = ""
        self.user = User.objects.create_user(user, email, pwd)

        self.exp = Experiment(
            title="test exp1", institution_name="monash", created_by=self.user
        )
        self.exp.save()

        self.dataset = Dataset(description="test dataset")
        self.dataset.save()

        self.datafile = DataFile(
            dataset=self.dataset, filename="testfile.txt", size=10, md5sum="bogus"
        )
        self.datafile.save()

        self.schema = Schema(
            namespace="http://test.namespace/exp/1",
            name="Text Exp Schema",
            type=Schema.EXPERIMENT,
        )
        self.schema.save()

        # Define some parameter names, one for each date type:
        self.pnames = {}

        for data_type_str in [
            "NUMERIC",
            "STRING",
            "URL",
            "LINK",
            "FILENAME",
            "DATETIME",
            "LONGSTRING",
            "JSON",
        ]:
            data_type = getattr(ParameterName, data_type_str)
            self.pnames[data_type] = ParameterName(
                schema=self.schema,
                name=data_type_str,
                full_name=data_type_str,
                data_type=getattr(ParameterName, data_type_str),
            )
            if data_type == ParameterName.NUMERIC:
                self.pnames[data_type].units = "items"
            self.pnames[data_type].save()

        self.pname_image_file = ParameterName(
            schema=self.schema,
            name="image file",
            full_name="Thumbnail image file parameter",
            data_type=ParameterName.FILENAME,
            units="image",
        )
        self.pname_image_file.save()

    def tearDown(self):
        self.exp.delete()
        self.user.delete()
        self.schema.delete()

    def test_experiment_parameter_get(self):
        """
        Test the Parameter class's get() method which should
        return an appropriate string representation of the
        parameter which depends on the parameter's data type:

        NUMERIC, STRING, URL, LINK, FILENAME, DATETIME, LONGSTRING or JSON
        """
        exp_parameterset = ExperimentParameterSet(
            schema=self.schema, experiment=self.exp
        )
        exp_parameterset.save()

        # NUMERIC
        exp_numeric_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.NUMERIC],
            numerical_value=123.456,
        )
        # units = "items" is set in this test case class's setUp method
        self.assertEqual(exp_numeric_param.get(), "123.456 items")

        # STRING
        exp_string_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.STRING],
            string_value="value1",
        )
        self.assertEqual(exp_string_param.get(), "value1")
        self.assertEqual(self.pnames[ParameterName.STRING].name, "STRING")
        # We wouldn't usually use an all uppercase parameter name like STRING,
        # but in this case, the STRING parameter name was populated
        # automatically in the setUp method.
        self.assertEqual(str(exp_string_param), "Experiment Param: STRING=value1")

        # URL
        url = "http://example.com/"
        exp_url_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.URL],
            string_value=url,
        )
        self.assertEqual(exp_url_param.get(), "<a href='%s'>%s</a>" % (url, url))

        # LINK
        # See also: test_link_urls
        exp_link_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset, name=self.pnames[ParameterName.LINK]
        )
        exp_url = self.exp.get_absolute_url()  # /experiment/view/1/
        exp_link_param.set_value(exp_url)
        exp_link_param.save()
        self.assertEqual(
            exp_link_param.get(), "<a href='%s'>%s</a>" % (exp_url, exp_url)
        )
        self.assertEqual(exp_link_param.link_url, exp_url)

        # FILENAME
        # See also: test_image_filename_parameters
        exp_filename_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.FILENAME],
            string_value="image.png",
        )
        exp_filename_param.string_value = "testfile.txt"
        self.assertEqual(exp_filename_param.get(), "testfile.txt")

        # DATETIME
        now = timezone.now()
        exp_datetime_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.DATETIME],
            datetime_value=now,
        )
        local_tz = pytz.timezone(settings.TIME_ZONE)
        now_str = now.astimezone(tz=local_tz).strftime("%c")
        self.assertEqual(exp_datetime_param.get(), now_str)

        # LONGSTRING
        exp_longstring_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.LONGSTRING],
            string_value="long value1",
        )
        self.assertEqual(exp_longstring_param.get(), "long value1")

        # JSON
        exp_json_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.JSON],
            string_value="[1, 2, 3]",
        )
        self.assertEqual(exp_json_param.get(), [1, 2, 3])

    def test_image_filename_parameters(self):
        """
        When a FILENAME parameter refers to a thumbanil image file,
        MyTardis can generate a HTML for displaying that image.

        This method tests the generation of the image HTML
        """
        exp_parameterset = ExperimentParameterSet(
            schema=self.schema, experiment=self.exp
        )
        exp_parameterset.save()

        exp_image_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pname_image_file,
            string_value="image.png",
        )
        expected_image_url = (
            "<a href='/display/ExperimentImage/load/%s/' target='_blank'>"
            "<img style='width: 300px;'"
            " src='/display/ExperimentImage/load/%s/' />"
            "</a>" % (exp_image_param.id, exp_image_param.id)
        )
        self.assertEqual(exp_image_param.get(), expected_image_url)

        dataset_parameterset = DatasetParameterSet(
            schema=self.schema, dataset=self.dataset
        )
        dataset_parameterset.save()

        dataset_image_param = DatasetParameter.objects.create(
            parameterset=dataset_parameterset,
            name=self.pname_image_file,
            string_value="image.png",
        )
        expected_image_url = (
            "<a href='/display/DatasetImage/load/%s/' target='_blank'>"
            "<img style='width: 300px;'"
            " src='/display/DatasetImage/load/%s/' />"
            "</a>" % (dataset_image_param.id, dataset_image_param.id)
        )
        self.assertEqual(dataset_image_param.get(), expected_image_url)

        datafile_parameterset = DatafileParameterSet(
            schema=self.schema, datafile=self.datafile
        )
        datafile_parameterset.save()

        datafile_image_param = DatafileParameter.objects.create(
            parameterset=datafile_parameterset,
            name=self.pname_image_file,
            string_value="image.png",
        )
        expected_image_url = (
            "<a href='/display/DatafileImage/load/%s/' target='_blank'>"
            "<img style='width: 300px;'"
            " src='/display/DatafileImage/load/%s/' />"
            "</a>" % (datafile_image_param.id, datafile_image_param.id)
        )
        self.assertEqual(datafile_image_param.get(), expected_image_url)

    def test_link_urls(self):
        """
        Test URLs generated for parameters which link to MyTardis model records
        """
        exp_parameterset = ExperimentParameterSet(
            schema=self.schema, experiment=self.exp
        )
        exp_parameterset.save()
        exp_link_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset, name=self.pnames[ParameterName.LINK]
        )
        exp_url = self.exp.get_absolute_url()  # /experiment/view/1/
        exp_link_param.set_value(exp_url)
        exp_link_param.save()
        self.assertEqual(
            exp_link_param.get(), "<a href='%s'>%s</a>" % (exp_url, exp_url)
        )
        self.assertEqual(exp_link_param.link_url, exp_url)

        dataset_parameterset = DatasetParameterSet(
            schema=self.schema, dataset=self.dataset
        )
        dataset_parameterset.save()
        dataset_link_param = DatasetParameter.objects.create(
            parameterset=dataset_parameterset, name=self.pnames[ParameterName.LINK]
        )
        dataset_url = self.dataset.get_absolute_url()  # /dataset/1/
        dataset_link_param.set_value(dataset_url)
        dataset_link_param.save()
        self.assertEqual(
            dataset_link_param.get(), "<a href='%s'>%s</a>" % (dataset_url, dataset_url)
        )
        self.assertEqual(dataset_link_param.link_url, dataset_url)

        # DataFile link parameters are rarely used, but if they
        # are, they link to the DataFile's dataset view
        datafile_parameterset = DatafileParameterSet(
            schema=self.schema, datafile=self.datafile
        )
        datafile_parameterset.save()
        datafile_link_param = DatafileParameter.objects.create(
            parameterset=datafile_parameterset, name=self.pnames[ParameterName.LINK]
        )
        dataset_url = self.dataset.get_absolute_url()  # /dataset/1/
        datafile_link_param.set_value(dataset_url)
        datafile_link_param.save()
        self.assertEqual(
            datafile_link_param.get(),
            "<a href='%s'>%s</a>" % (dataset_url, dataset_url),
        )
        self.assertEqual(datafile_link_param.link_url, dataset_url)

        datafile_link_param.link_gfk = None
        datafile_link_param.save()
        datafile_link_param.string_value = "not a link"
        datafile_link_param.save()
        self.assertEqual(datafile_link_param.link_url, "not a link")

    def test_permissions_checks(self):
        """
        Test permissions checks, used by
        tardis.tardis_portal.auth.authorisation
        """
        exp_parameterset = ExperimentParameterSet(
            schema=self.schema, experiment=self.exp
        )
        exp_parameterset.save()
        self.assertTrue(exp_parameterset._has_view_perm(self.user))
        self.assertTrue(exp_parameterset._has_change_perm(self.user))
        self.assertTrue(exp_parameterset._has_delete_perm(self.user))

        exp_param = ExperimentParameter.objects.create(
            parameterset=exp_parameterset,
            name=self.pnames[ParameterName.STRING],
            string_value="value1",
        )
        self.assertTrue(exp_param._has_view_perm(self.user))
        self.assertTrue(exp_param._has_change_perm(self.user))
        self.assertTrue(exp_param._has_delete_perm(self.user))
