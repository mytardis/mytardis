from celery.task import task
from datetime import datetime
from django.contrib.auth.models import User
from django.conf import settings
from .models import Credential, RemoteHost
from tardis.tardis_portal.models import Experiment, Dataset, DataFile


@task
def push_experiment_to_host(
    user_id, credential_id, remote_host_id, experiment_id
):
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
        notify_user(user_id, remote_host_id, success=True)
    except:
        notify_user(user_id, remote_host_id, success=False)
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
        notify_user(user_id, remote_host_id, success=True)
    except:
        notify_user(user_id, remote_host_id, success=False)
        raise


@task
def push_datafile_to_host(user_id, credential_id, remote_host_id, datafile_id):
    try:
        file_to_copy = [([], DataFile.objects.get(pk=datafile_id))]
        do_file_copy(credential_id, remote_host_id, file_to_copy)
        notify_user(user_id, remote_host_id, success=True)
    except:
        notify_user(user_id, remote_host_id, success=False)
        raise


def notify_user(user_id, remote_host_id, success=True):
    remote_host = RemoteHost.objects.get(pk=remote_host_id)
    user = User.objects.get(pk=user_id)
    if success:
        subject = '[TARDIS] Data pushed successfully'
        message = ('Your recent push-to request was completed successfully!\n'
                   'Log in to %s to access the requested data.')
    else:
        subject = '[TARDIS] Data push failed'
        message = ('Your recent push-to request to %s encountered an error and'
                   ' could not be completed.\n'
                   'Contact your system administrator for more information.')
    message %= remote_host.nickname
    user.email_user(subject, message,
                    from_email=getattr(settings, 'PUSH_TO_FROM_EMAIL', None))


def do_file_copy(credential_id, remote_host_id, datafile_map):

    base_dir = [
        'mytardis-data', datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")
    ]

    credential = Credential.objects.get(pk=credential_id)
    ssh = credential.get_client_for_host(
        RemoteHost.objects.get(
            pk=remote_host_id))
    sftp_client = ssh.open_sftp()

    def make_dirs(dir_list):
        full_path = ''
        for directory in dir_list:
            if full_path:
                full_path += '/' + directory
            else:
                full_path = directory
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
