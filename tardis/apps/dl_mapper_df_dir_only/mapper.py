"""
File mapper that works for files stored in deep directory structures.
It recreates the structure as stored in the datafile directory
"""
import os


def df_dir_only(datafile, rootdir):
    dataset = datafile.dataset
    exp = dataset.get_first_experiment()
    filepath = os.path.join(
        datafile.directory or dataset.description, datafile.filename
    )
    if rootdir != "datasets":
        return os.path.join(rootdir, filepath)
    if exp is not None:
        return os.path.join(exp.title, filepath)
    raise Exception
