#
# Copyright (c) 2012, Centre for Microscopy and Microanalysis
#   (University of Queensland, Australia)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the University of Queensland nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
#

import math

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
        return self._filter_map_sort(datafiles, score_it)

    def score_datafiles_in_experiment(self, experiment):
        from tardis.tardis_portal.models import Dataset_File
        def score_it(datafile):
            ds_score = self.dataset_score(datafile.dataset)
            return (datafile, ds_score * self.datafile_score(datafile))
        datafiles = Dataset_File.objects.\
            filter(dataset__experiments__id=experiment.id, verified=True)
        return self._filter_map_sort(datafiles, score_it)

    def score_all_datafiles(self):
        from tardis.tardis_portal.models import Dataset_File
        def score_it(datafile):
            ds_score = self.dataset_score(datafile.dataset)
            return (datafile, ds_score * self.datafile_score(datafile))
        datafiles = Dataset_File.objects.filter(verified=True)
        return self._filter_map_sort(datafiles, score_it)

    def _filter_map_sort(self, datafiles, mapper):
        from tardis.tardis_portal.models import Dataset_File
        def get_score(tpl):
            return tpl[1]        
        return sorted(map(mapper, filter(Dataset_File.is_local, datafiles)),
                      None, get_score, True)

    def datafile_score(self, datafile):
        try:
            return math.log10(float(datafile.size))
        except:
            # Size is zero ... something else we can't cope with
            return 0.0

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

    
