from haystack.forms import ModelSearchForm

from tardis.tardis_portal.models import Experiment, Dataset, DataFile


class GroupedSearchForm(ModelSearchForm):

    def search(self, *args, **kwargs):
        user = kwargs.pop('user')
        sqs = super(GroupedSearchForm, self).search().highlight().models(
            *self.get_models())
        exp_ids = Experiment.safe.all(user).values_list('id', flat=True)
        queryset = sqs.filter(experiment_id_stored__in=exp_ids)
        for result in queryset:
            if isinstance(result.experiment_id_stored, list):
                result.experiment_id_stored = list(
                    set(result.experiment_id_stored).intersection(exp_ids))
                result.experiments = Experiment.objects.filter(
                    id__in=result.experiment_id_stored)
            else:
                result.experiments = Experiment.objects.filter(
                    id=result.experiment_id_stored)
        return queryset
