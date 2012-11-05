import math
#from tardis.tardis_portal.models import Dataset_File, Dataset, Experiment
#from tardis.apps.migration.models import UserPriority, GroupPriority, \
#    get_user_priority, get_group_priority

class MigrationScorer:
    """
    This class implements the algorithms for scoring a group of Datafiles
    to figure which ones to migrate if we are running short of space.  The 
    general rule is that Datafiles with the largest scores are most eligible
    for migration to slower / cheaper storage.

    A MigrationScorer instance memoizes the score contributions of users
    and experiments and datasets.  It is therefore stateful. 
    """

    dataset_scores = {}
    experiment_scores = {}
    user_scores = {}
    group_scores = {}
    
    def score_datafile(self, datafile):
        return self.datafile_score(datafile) * \
            self.dataset_score(datafile.dataset)

    def score_datafiles_in_dataset(self, dataset):
        from tardis.tardis_portal.models import Dataset_File
        ds_score = self.dataset_score(dataset)
        def score_it(datafile):
            return (datafile, ds_score * self.datafile_score(datafile))
        datafiles = Dataset_File.objects.filter(dataset=dataset, verified=True)
        return map(score_it, filter(Dataset_File.is_local, datafiles))

    def score_datafiles_in_experiment(self, experiment):
        from tardis.tardis_portal.models import Dataset_File
        def score_it(datafile):
            ds_score = self.dataset_score(datafile.dataset)
            return (datafile, ds_score * self.datafile_score(datafile))
        datafiles = Dataset_File.objects.\
            filter(dataset__experiments__id=experiment.id, verified=True)
        return map(score_it, filter(Dataset_File.is_local, datafiles))

    def score_all_datafiles(self):
        from tardis.tardis_portal.models import Dataset_File
        def score_it(datafile):
            ds_score = self.dataset_score(datafile.dataset)
            return (datafile, ds_score * self.datafile_score(datafile))
        datafiles = Dataset_File.objects.filter(verified=True)
        return map(score_it, filter(Dataset_File.is_local, datafiles))

    def datafile_score(self, datafile):
        return math.log10(float(datafile.size))

    def dataset_score(self, dataset):
        from tardis.tardis_portal.models import Dataset
        try:
            return self.dataset_scores[dataset.id]
        except KeyError:
            pass
        max_score = 0.0
        for exp in Dataset.objects.get(id=dataset.id).experiments.all():
            score = self.experiment_score(exp)
            if score > max_score:
                max_score = score
        self.dataset_scores[dataset.id] = max_score
        return max_score

    def experiment_score(self, experiment):
        try:
            return self.experiment_scores[experiment.id]
        except KeyError:
            pass
        max_score = 0.0
        for user in experiment.get_owners():
            score = self.user_score(user)
            if score > max_score:
                max_score = score
        self.experiment_scores[experiment.id] = max_score
        return max_score
    
    def user_score(self, user):
        from tardis.apps.migration.models import get_user_priority
        try:
            return self.user_scores[user.id]
        except KeyError:
            pass
        priority = get_user_priority(user)
        score = [5.0, 2.0, 1.0, 0.5, 0.2][priority]
        self.user_scores[user.id] = score
        return score
        
   
    def group_score(self, group):
        return 1.0

    
