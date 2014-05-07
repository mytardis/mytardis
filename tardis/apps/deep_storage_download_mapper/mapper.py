'''
File mapper that works for files stored in deep directory structures.
It replicates the structure as stored in the File Replica
'''
import os


def deep_storage_mapper(datafile, rootdir):
    dataset = datafile.dataset
    exp = dataset.get_first_experiment()
    filepath = os.path.join(dataset.directory or '', dataset.description,
                            datafile.directory or '', datafile.filename)
    if rootdir != 'datasets':
        return os.path.join(rootdir, filepath)
    elif exp is not None:
        return os.path.join(exp.directory or '', exp.title, filepath)
    else:
        raise Exception
