import pytz

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import is_aware, make_aware

from .models.experiment import Experiment
from .models.dataset import Dataset
from .models.datafile import DataFile

LOCAL_TZ = pytz.timezone(settings.TIME_ZONE)


class ParameterSetManager(object):

    parameterset = None
    parameters = None  # queryset of parameters
    blank_param = None

    # parameterset OR schema / datafile / dataset / experiment
    # delete dataset creation code
    # make parameterset / object arguments generic and test type
    # create function to return generic parameter type for setting/getting
    #
    # 2011/07/20 (Ryan Braganza)
    # changed type checking from:
    #     type(self.parameterset).__name__ == 'ClassName'
    # to:
    #     isinstance(self.parameterset, Class)
    # This is to solve an issue with models using deferred fields.
    # When using deferred fields, a subclass is used, so the class name
    # will not match when using type(self.parameterset).__name__
    # isinstance deals with inheritance appropriately here
    def __init__(self, parameterset=None, parentObject=None, schema=None):
        """
        instantiate new task or existing ParameterSet
        :param ParameterSet parameterset: optional parameter to instanciate
          task from metadata, will be tested for completeness and copied into
          new task if complete
        :param object parentObject:
        :param string schema: Schema namespace
        :raises TypeError:
        """
        from .models.parameters import (
            DatasetParameterSet,
            DatafileParameterSet,
            ExperimentParameterSet,
            DatasetParameter,
            DatafileParameter,
            ExperimentParameter,
            ParameterSet,
        )

        if issubclass(type(self), ParameterSet):
            pass
        elif parameterset:
            self.parameterset = parameterset
            self.schema = self.parameterset.schema
            self.namespace = self.schema.namespace

            if isinstance(self.parameterset, DatafileParameterSet):
                self.parameters = DatafileParameter.objects.filter(
                    parameterset=self.parameterset
                ).order_by("name__full_name")

                self.blank_param = DatafileParameter

            elif isinstance(self.parameterset, DatasetParameterSet):
                self.parameters = DatasetParameter.objects.filter(
                    parameterset=self.parameterset
                ).order_by("name__full_name")

                self.blank_param = DatasetParameter

            elif isinstance(self.parameterset, ExperimentParameterSet):
                self.parameters = ExperimentParameter.objects.filter(
                    parameterset=self.parameterset
                ).order_by("name__full_name")

                self.blank_param = ExperimentParameter

            else:
                raise TypeError("Invalid parameterset object given.")

        elif parentObject and schema:

            self.namespace = schema

            if isinstance(parentObject, DataFile):
                self.parameterset = DatafileParameterSet(
                    schema=self.get_schema(), datafile=parentObject
                )

                self.parameterset.save()

                self.parameters = DatafileParameter.objects.filter(
                    parameterset=self.parameterset
                )

                self.blank_param = DatafileParameter

            elif isinstance(parentObject, Dataset):
                self.parameterset = DatasetParameterSet(
                    schema=self.get_schema(), dataset=parentObject
                )

                self.parameterset.save()

                self.parameters = DatasetParameter.objects.filter(
                    parameterset=self.parameterset
                )

                self.blank_param = DatasetParameter

            elif isinstance(parentObject, Experiment):
                self.parameterset = ExperimentParameterSet(
                    schema=self.get_schema(), experiment=parentObject
                )

                self.parameterset.save()

                self.parameters = ExperimentParameter.objects.filter(
                    parameterset=self.parameterset
                )

                self.blank_param = ExperimentParameter

            else:
                raise TypeError(
                    "Invalid parent object."
                    + "Must be an experiment/dataset/datafile not "
                    + str(type(parentObject))
                )

        else:
            raise TypeError("Missing arguments")

    def get_schema(self):
        from .models.parameters import Schema

        try:
            schema = Schema.objects.get(namespace=self.namespace)
        except ObjectDoesNotExist:
            schema = Schema()
            schema.namespace = self.namespace
            schema.save()
            self.schema = schema
        return schema

    def get_param(self, parname, value=False):
        par = self.parameters.get(name__name=parname)
        if value:
            if par.name.isNumeric():
                return par.numerical_value
            if par.name.isDateTime():
                if is_aware(par.datetime_value):
                    return par.datetime_value
                return make_aware(par.datetime_value, LOCAL_TZ, settings.IS_DST)
            return par.string_value
        return par

    def get_param_sens_flag(self, parname):
        par_flag = self.parameters.get(name__name=parname).name.sensitive
        return par_flag

    def get_params(self, parname, value=False):
        pars = self.parameters.filter(name__name=parname)
        if value:
            if pars and pars[0].name.isNumeric():
                return [par.numerical_value for par in pars]
            return [par.string_value for par in pars]
        return pars

    def set_param(self, parname, value, fullparname=None, example_value=None):
        try:
            param = self.get_param(parname)
        except ObjectDoesNotExist:
            param = self.blank_param()
            param.parameterset = self.parameterset
            param.name = self._get_create_parname(
                parname, fullparname, example_value=example_value
            )
        param.set_value(value)
        param.save()
        return param.id

    def new_param(self, parname, value, fullparname=None):
        param = self.blank_param()
        param.parameterset = self.parameterset
        param.name = self._get_create_parname(parname, fullparname)
        param.string_value = value
        param.save()
        param.set_value(value)
        param.save()
        return param.id

        # use this one from post data

    def set_param_list(self, parname, value_list, fullparname=None):
        self.delete_params(parname)
        for value in value_list:
            if value is not None:
                self.new_param(parname, value, fullparname)

    def set_params_from_dict(self, params_dict):
        for (key, value) in params_dict.items():
            if isinstance(value, list):
                self.set_param_list(key, value)
            else:
                if value is not None:
                    self.delete_params(key)
                    self.set_param(key, value)

    def delete_params(self, parname):
        params = self.get_params(parname)
        for param in params:
            param.delete()

    def delete_all_params(self):
        for param in self.parameters:
            param.delete()

    def _get_create_parname(self, parname, fullparname=None, example_value=None):
        from .models.parameters import ParameterName

        try:
            paramName = ParameterName.objects.get(
                name=parname, schema__id=self.get_schema().id
            )
        except ObjectDoesNotExist:
            paramName = ParameterName()
            paramName.schema = self.get_schema()
            paramName.name = parname
            if fullparname:
                paramName.full_name = fullparname
            else:
                paramName.full_name = parname
            if example_value:
                try:
                    float(example_value)
                    paramName.data_type = ParameterName.NUMERIC
                except (TypeError, ValueError):
                    paramName.data_type = ParameterName.STRING
            else:
                paramName.data_type = ParameterName.STRING
            paramName.is_searchable = True
            paramName.save()
        return paramName
