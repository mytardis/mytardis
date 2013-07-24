'''
File mapper that works for files stored in deep directory structures.
It replicates the structure as stored in the File Replica
'''
import os


def deep_storage_mapper(datafile, rootdir):
    url = datafile.get_preferred_replica().url
    expid = str(datafile.dataset.get_first_experiment().id)
    if rootdir != 'datasets':
        return url
    elif expid is not None:
        return os.path.join(rootdir,
                            os.path.relpath(url, expid))
    else:
        raise Exception
