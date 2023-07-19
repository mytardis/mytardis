# -*- coding: utf-8 -*-
"""
test_parameter.py

.. moduleauthor::  Russell Sim <russell.sim@monash.edu>
.. moduleauthor::  James Wettenhall <james.wettenhall@monash.edu>

"""
import os

from tardis.tardis_portal.models import (
    DataFile,
    DatafileParameter,
    DatafileParameterSet,
    Dataset,
    DatasetParameter,
    DatasetParameterSet,
    Experiment,
    ExperimentParameter,
    ExperimentParameterSet,
    ParameterName,
    Schema,
)

from . import ModelTestCase


class ParameterTestCase(ModelTestCase):

    def test_parameter(self):
        exp = Experiment(
            title='test exp1',
            institution_name='Australian Synchrotron',
            approved=True,
            created_by=self.user,
            public_access=Experiment.PUBLIC_ACCESS_NONE,
        )
        exp.save()

        dataset = Dataset(description="dataset description")
        dataset.save()
        dataset.experiments.add(exp)
        dataset.save()

        df_file = DataFile(dataset=dataset,
                           filename='file.txt',
                           size=42,
                           md5sum='bogus')
        df_file.save()

        df_schema = Schema(
            namespace='http://www.cern.ch/felzmann/schema1.xml',
            type=Schema.DATAFILE)
        df_schema.save()

        ds_schema = Schema(
            namespace='http://www.cern.ch/felzmann/schema2.xml',
            type=Schema.DATASET)
        ds_schema.save()

        exp_schema = Schema(
            namespace='http://www.cern.ch/felzmann/schema3.xml',
            type=Schema.EXPERIMENT)
        exp_schema.save()

        df_parname = ParameterName(
            schema=df_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=ParameterName.FILENAME)
        df_parname.save()

        ds_parname = ParameterName(
            schema=ds_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=ParameterName.FILENAME)
        ds_parname.save()

        exp_parname = ParameterName(
            schema=exp_schema,
            name='name',
            full_name='full_name',
            units='image/jpg',
            data_type=ParameterName.FILENAME)
        exp_parname.save()

        df_parset = DatafileParameterSet(schema=df_schema,
                                         datafile=df_file)
        df_parset.save()

        ds_parset = DatasetParameterSet(schema=ds_schema,
                                        dataset=dataset)
        ds_parset.save()

        exp_parset = ExperimentParameterSet(schema=exp_schema,
                                            experiment=exp)
        exp_parset.save()

        with self.settings(METADATA_STORE_PATH=os.path.dirname(__file__)):
            filename = 'test.jpg'
            df_parameter = DatafileParameter(name=df_parname,
                                             parameterset=df_parset,
                                             string_value=filename)
            df_parameter.save()

            ds_parameter = DatasetParameter(name=ds_parname,
                                            parameterset=ds_parset,
                                            string_value=filename)
            ds_parameter.save()

            exp_parameter = ExperimentParameter(name=exp_parname,
                                                parameterset=exp_parset,
                                                string_value=filename)
            exp_parameter.save()

            self.assertEqual(
                "<a href='/display/DatafileImage/load/%i/' target='_blank'><img style='width: 300px;' src='/display/DatafileImage/load/%i/' /></a>" %  # noqa
                (df_parameter.id, df_parameter.id), df_parameter.get())

            self.assertEqual(
                "<a href='/display/DatasetImage/load/%i/' target='_blank'><img style='width: 300px;' src='/display/DatasetImage/load/%i/' /></a>" %  # noqa
                (ds_parameter.id, ds_parameter.id), ds_parameter.get())

            self.assertEqual(
                "<a href='/display/ExperimentImage/load/%i/' target='_blank'><img style='width: 300px;' src='/display/ExperimentImage/load/%i/' /></a>" %   # noqa
                (exp_parameter.id, exp_parameter.id), exp_parameter.get())
