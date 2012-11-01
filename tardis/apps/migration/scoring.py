
class MigrationScorer:
    
    def score_datafile(self, datafile):
        return self.datafile_score(datafile) * \
            self.dataset_score(datafile.dataset)

    def score_datafiles_in_dataset(self, dataset):
        ds_score = self.dataset_score(dataset)
        def score_it(datafile):
            return (datafile.id, ds_score * self.datafile_score(datafile))
        return map(score_it, Dataset_File.objects.filter(dataset=dataset))

    def score_datafiles_in_experiment(self, experiment):
        raise NotImplementedError

    def score_all_datafiles(self, experiment):
        raise NotImplementedError

    def score_datafiles_in_experiment(self, experiment):
        raise NotImplementedError

    def datafile_score(self, datafile):
        return math.log10(datafile.size)

    def dataset_score(self, dataset):
        return 1.0

    def experiment_score(self, experiment):
        return 1.0
    
    def user_score(self, user):
        raise 1.0
   
    def group_score(self, group):
        raise 1.0

    
