"""
test_parameters.py

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>
"""
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from tardis.tardis_portal.models.parameters import (
    ParameterName,
    Schema,
)
from ..models import Project, ProjectParameter, ProjectParameterSet


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
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

        self.proj = Project(
            name="test proj1", created_by=self.user, principal_investigator=self.user
        )
        self.proj.save()

        self.schema = Schema(
            namespace="http://test.namespace/proj/1",
            name="Text Proj Schema",
            type=Schema.PROJECT,
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
        self.proj.delete()
        self.user.delete()
        self.schema.delete()

    def test_image_filename_parameters(self):
        """
        When a FILENAME parameter refers to a thumbnail image file,
        MyTardis can generate a HTML for displaying that image.

        This method tests the generation of the image HTML
        """
        proj_parameterset = ProjectParameterSet(schema=self.schema, project=self.proj)
        proj_parameterset.save()

        proj_image_param = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=self.pname_image_file,
            string_value="image.png",
        )
        expected_image_url = (
            "<a href='/project/display/ProjectImage/load/%s/' target='_blank'>"
            "<img style='width: 300px;'"
            " src='/project/display/ProjectImage/load/%s/' />"
            "</a>" % (proj_image_param.id, proj_image_param.id)
        )
        self.assertEqual(proj_image_param.get(), expected_image_url)

    def test_link_urls(self):
        """
        Test URLs generated for parameters which link to MyTardis model records
        """
        proj_parameterset = ProjectParameterSet(schema=self.schema, project=self.proj)
        proj_parameterset.save()
        proj_link_param = ProjectParameter.objects.create(
            parameterset=proj_parameterset, name=self.pnames[ParameterName.LINK]
        )
        proj_url = self.proj.get_absolute_url()  # /project/view/1/
        proj_link_param.set_value(proj_url)
        proj_link_param.save()
        self.assertEqual(
            proj_link_param.get(), "<a href='%s'>%s</a>" % (proj_url, proj_url)
        )
        self.assertEqual(proj_link_param.link_url, proj_url)

    def test_permissions_checks(self):
        """
        Test permissions checks, used by
        tardis.tardis_portal.auth.authorisation
        """
        proj_parameterset = ProjectParameterSet(schema=self.schema, project=self.proj)
        proj_parameterset.save()
        self.assertTrue(proj_parameterset._has_view_perm(self.user))
        self.assertTrue(proj_parameterset._has_change_perm(self.user))
        self.assertTrue(proj_parameterset._has_delete_perm(self.user))

        proj_param = ProjectParameter.objects.create(
            parameterset=proj_parameterset,
            name=self.pnames[ParameterName.STRING],
            string_value="value1",
        )
        self.assertTrue(proj_param._has_view_perm(self.user))
        self.assertTrue(proj_param._has_change_perm(self.user))
        self.assertTrue(proj_param._has_delete_perm(self.user))
