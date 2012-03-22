from os import path

from tardis.tardis_portal.models import Experiment, Dataset_File


class IntegrityCheck(object):
    def __init__(self, experiment_or_id):
        self.experiment = experiment_or_id
        if not isinstance(self.experiment, Experiment):
            self.experiment = Experiment.objects.get(pk=experiment_or_id)

    # enrich the dataset information with details about files on disk etc
    def get_datafiles_integrity(self):
        """Check whether all datafiles belonging to this experiment actually exist on disk.
        Return status of each as a dictionary."""

        datafiles = Dataset_File.objects.filter(dataset__experiment__pk=self.experiment.id)

        output = { 'files_ok': 0, 'files_missing': 0, 'files_incomplete': 0, 'datafiles': {} }
        for datafile in datafiles.iterator():
            filename = datafile.get_absolute_filepath()
            exists = path.exists(filename)
            size = path.getsize(filename) if exists else -1
            complete = (size == int(datafile.size))
            output['datafiles'][datafile.id] = {
                                'url':   datafile.url,
                                'found': exists,
                                'size':  size,
                                'complete': complete
                                }

            if not exists:
                output['files_missing'] += 1
            elif not complete:
                output['files_incomplete'] += 1
            else:
                output['files_ok'] += 1
        return output

    def all_files_complete(self):
        results = self.get_datafiles_integrity()
        return results['files_missing'] == 0 and results['files_incomplete'] == 0

