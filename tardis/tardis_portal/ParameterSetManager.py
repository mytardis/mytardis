from django.core.exceptions import ObjectDoesNotExist

from tardis.tardis_portal.models import DatasetParameterSet
from tardis.tardis_portal.models import ParameterName
from tardis.tardis_portal.models import DatasetParameter
from tardis.tardis_portal.models import Dataset
from tardis.tardis_portal.models import Schema


class ParameterSetManager():
    parameterset = None
    parameters = None # queryset of parameters
    parentObject = None

    # parameterset OR schema / datafile / dataset / experiment
    # delete dataset creation code
    # make parameterset / object arguments generic and test type
    def __init__(self, dataset=None, dataset_id=None,
                 description="", experiment_id=None):
        """
        instantiate new task or existing task
        :param dataset: optional parameter to instanciate task from
          metadata, will be tested for completeness and copied into
          new task if complete
        :type dataset: Dataset
        """
        if dataset:
            self.dataset = dataset
        elif dataset_id:
            self.dataset = Dataset.objects.get(pk=dataset_id)
        else:
            if description == "":
                raise TypeError("No description given")
            if not experiment_id:
                raise TypeError("No experiment id given")
            self.dataset = Dataset()
            self.dataset.experiment_id = experiment_id
            self.dataset.description = description
            self.dataset.save()
        try:
            self.DPS = DatasetParameterSet.objects.get(
                dataset=self.dataset,
                schema__namespace__endswith=self.type)
        except ObjectDoesNotExist:
            self.DPS = DatasetParameterSet()
            self.DPS.dataset = self.dataset
            self.DPS.schema = self.get_schema()
            self.DPS.save()
        self.parameters = DatasetParameter.objects.filter(
            parameterset=self.DPS)

    def get_schema(self):
        try:
            schema = Schema.objects.get(
                namespace="%s/%s" % (self.baseschema, self.type))
        except ObjectDoesNotExist:
            schema = Schema()
            schema.namespace = "%s/%s" % (self.baseschema, self.type)
            schema.save()
        return schema

    def get_param(self, parname, value=False):
        par = self.parameters.get(name__name=parname)
        if value:
            if par.name.is_numeric:
                return par.numerical_value
            else:
                return par.string_value
        return par

    def get_params(self, parname, value=False):
        pars = self.parameters.filter(name__name=parname)
        if value:
            if len(pars) > 0 and pars[0].name.is_numeric:
                return [par.numerical_value
                        for par in pars]
            else:
                return [par.string_value
                        for par in pars]
        return pars

    def set_param(self, parname, value, fullparname=None):
        try:
            param = self.get_param(parname)
        except ObjectDoesNotExist:
            param = DatasetParameter()
            param.parameterset = self.DPS
            param.name = self._get_create_parname(parname, fullparname)
            param.string_value = value
            param.save()
        if param.name.is_numeric:
            param.numerical_value = float(value)
        else:
            param.string_value = str(value)
        param.save()

    def new_param(self, parname, value, fullparname=None):
        param = DatasetParameter()
        param.parameterset = self.DPS
        param.name = self._get_create_parname(parname, fullparname)
        param.string_value = value
        param.save()
        if param.name.is_numeric:
            param.numerical_value = float(value)
        else:
            param.string_value = str(value)
        param.save()

        # use this one from post data
    def set_param_list(self, parname, value_list, fullparname=None):
        self.delete_params(parname)
        for value in value_list:
            self.new_param(parname, value, fullparname)

    def set_params_from_dict(self, dict):
        print type(dict)
        for (key, value) in dict.iteritems():
            if type(value) is list:
                self.set_param_list(key, value)
            else:
                self.set_param(key, value)

    def delete_params(self, parname):
        params = self.get_params(parname)
        for param in params:
            param.delete()

    def _get_create_parname(self, parname,
                            fullparname=None, example_value=None):
        try:
            paramName = ParameterName.objects.get(name=parname,
                                                  schema=self.get_schema())
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
                    paramName.is_numeric = True
                except (TypeError, ValueError):
                    paramName.is_numeric = False
            else:
                paramName.is_numeric = False
            paramName.is_searchable = True
            paramName.save()
        return paramName
