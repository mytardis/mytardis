from celery.task import task
from datetime import datetime
from django.contrib.auth.models import User
from tardis.apps.push_to.models import Credential, RemoteHost
from tardis.tardis_portal.models import Experiment, Dataset, DataFile


@task
def push_experiment_to_host(
        user_id,
        credential_id,
        remote_host_id,
        experiment_id):
    try:
        files_to_copy = []
        experiment = Experiment.objects.get(pk=experiment_id)
        datasets = Dataset.objects.filter(experiments=experiment)
        for ds in datasets:
            datafiles = DataFile.objects.filter(dataset=ds)
            path = [experiment.title, ds.description]
            for df in datafiles:
                files_to_copy.append((path, df))

        do_file_copy(credential_id, remote_host_id, files_to_copy)
        notify_user(user_id, success=True)
    except:
        notify_user(user_id, success=False)
        raise


@task
def push_dataset_to_host(user_id, credential_id, remote_host_id, dataset_id):
    try:
        files_to_copy = []
        datasets = Dataset.objects.filter(pk=dataset_id)
        for ds in datasets:
            datafiles = DataFile.objects.filter(dataset=ds)
            path = [ds.description]
            for df in datafiles:
                files_to_copy.append((path, df))

        do_file_copy(credential_id, remote_host_id, files_to_copy)
        notify_user(user_id, success=True)
    except:
        notify_user(user_id, success=False)
        raise


@task
def push_datafile_to_host(user_id, credential_id, remote_host_id, datafile_id):
    try:
        file_to_copy = [([], DataFile.objects.get(pk=datafile_id))]
        do_file_copy(credential_id, remote_host_id, file_to_copy)
        notify_user(user_id, success=True)
    except:
        notify_user(user_id, success=False)
        raise


def notify_user(user_id, success=True):
    user = User.objects.get(pk=user_id)
    if success:
        # Tell the user everything went okay
        pass
    else:
        # Tell the user things went badly
        pass


def do_file_copy(credential_id, remote_host_id, datafile_map):

    base_dir = [
        'mytardis-data',
        datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")]

    credential = Credential.objects.get(pk=credential_id)
    ssh = credential.get_client_for_host(
        RemoteHost.objects.get(
            pk=remote_host_id))
    sftp_client = ssh.open_sftp()

    def make_dirs(dir_list):
        full_path = ''
        for dir in dir_list:
            if full_path:
                full_path += '/' + dir
            else:
                full_path = dir
            try:
                sftp_client.stat(full_path)
            except IOError:  # Raised when the directory doesn't exist
                sftp_client.mkdir(full_path)

    make_dirs(base_dir)

    for (path, datafile) in datafile_map:
        if datafile.directory is not None:
            path += datafile.directory.split('/')
        path = base_dir + path
        path_str = '/'.join(path + [datafile.filename])
        make_dirs(path)
        sftp_client.putfo(datafile.file_object, path_str, datafile.size)
