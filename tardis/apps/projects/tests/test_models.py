# projectacl
# institution

# -*- coding: utf-8 -*-
"""
test_models.py

.. moduleauthor::  Mike Laverick <mike.laverick@auckland.ac.nz>

"""
import os
from unittest import skipIf

from django.conf import settings

from tardis.apps.projects.models import Project, ProjectParameter, ProjectParameterSet
from tardis.tardis_portal.models import (
    ParameterName,
    Schema,
)

from . import ModelTestCase


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ProjectTestCase(ModelTestCase):
    def test_project(self):
        proj = Project(
            name="test proj1", created_by=self.user, principal_investigator=self.user
        )
        proj.save()
        self.assertEqual(proj.name, "test proj1")
        self.assertEqual(proj.url, None)
        self.assertEqual(proj.created_by, self.user)
        self.assertEqual(proj.principal_investigator, self.user)
        self.assertEqual(proj.public_access, Project.PUBLIC_ACCESS_NONE)
        target_id = Project.objects.first().id
        self.assertEqual(
            proj.get_absolute_url(),
            "/project/view/%d/" % target_id,
            proj.get_absolute_url() + " != /project/view/%d/" % target_id,
        )


@skipIf(settings.ONLY_EXPERIMENT_ACLS is True, "skipping Micro ACL specific test")
class ParameterTestCase(ModelTestCase):
    def test_parameter(self):
        proj = Project(
            name="test proj1",
            created_by=self.user,
            principal_investigator=self.user,
            public_access=Project.PUBLIC_ACCESS_NONE,
        )
        proj.save()

        proj_schema = Schema(
            namespace="http://www.cern.ch/felzmann/schema3.xml", type=Schema.PROJECT
        )
        proj_schema.save()

        proj_parname = ParameterName(
            schema=proj_schema,
            name="name",
            full_name="full_name",
            units="image/jpg",
            data_type=ParameterName.FILENAME,
        )
        proj_parname.save()

        proj_parset = ProjectParameterSet(schema=proj_schema, project=proj)
        proj_parset.save()

        with self.settings(METADATA_STORE_PATH=os.path.dirname(__file__)):
            filename = "test.jpg"

            proj_parameter = ProjectParameter(
                name=proj_parname, parameterset=proj_parset, string_value=filename
            )
            proj_parameter.save()

            self.assertEqual(
                "<a href='/project/display/ProjectImage/load/%i/' target='_blank'><img style='width: 300px;' src='/project/display/ProjectImage/load/%i/' /></a>"
                % (proj_parameter.id, proj_parameter.id),  # noqa
                proj_parameter.get(),
            )
