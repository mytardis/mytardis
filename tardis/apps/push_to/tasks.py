from django.conf import settings
from django.contrib.auth.models import User

from tardis.tardis_portal.models import Experiment, Dataset, DataFile
from tardis.celery import tardis_app
from tardis.tardis_portal.util import split_path
from tardis.tardis_portal.util import get_filesystem_safe_experiment_name
from tardis.tardis_portal.util import get_filesystem_safe_dataset_name

from .models import Credential, RemoteHost


@tardis_app.task
def push_experiment_to_host(
        user_id, credential_id, remote_host_id, experiment_id, base_dir=None
):
    try:
        files_to_copy = []
        experiment = Experiment.objects.get(pk=experiment_id)
        experiment_name = get_filesystem_safe_experiment_name(experiment)
        datasets = Dataset.objects.filter(experiments=experiment)
        for ds in datasets:
            datafiles = DataFile.objects.filter(dataset=ds)
            dataset_description = get_filesystem_safe_dataset_name(ds)
            path = [experiment_name, dataset_description]
            for df in datafiles:
                files_to_copy.append((path, df))

        do_file_copy(credential_id, remote_host_id, files_to_copy, base_dir)
        notify_user(user_id, remote_host_id, success=True)
    except:
        notify_user(user_id, remote_host_id, success=False)
        raise


@tardis_app.task
def push_dataset_to_host(user_id, credential_id, remote_host_id, dataset_id,
                         base_dir=None):
    try:
        files_to_copy = []
        datasets = Dataset.objects.filter(pk=dataset_id)
        for ds in datasets:
            datafiles = DataFile.objects.filter(dataset=ds)
            dataset_description = get_filesystem_safe_dataset_name(ds)
            path = [dataset_description]
            for df in datafiles:
                files_to_copy.append((path, df))

        do_file_copy(credential_id, remote_host_id, files_to_copy, base_dir)
        notify_user(user_id, remote_host_id, success=True)
    except:
        notify_user(user_id, remote_host_id, success=False)
        raise


@tardis_app.task
def push_datafile_to_host(user_id, credential_id, remote_host_id, datafile_id,
                          base_dir=None):
    try:
        file_to_copy = [([], DataFile.objects.get(pk=datafile_id))]
        do_file_copy(credential_id, remote_host_id, file_to_copy, base_dir)
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
                    from_email=getattr(settings, 'PUSH_TO_FROM_EMAIL', None), fail_silently=True)


def make_dirs(sftp_client, dir_list):
    full_path = ''
    for directory in dir_list:
        if full_path:
            full_path += directory.rstrip('/') + '/'
        elif directory:
            full_path = directory.rstrip('/') + '/'
        else:
            full_path = '/'

        try:
            sftp_client.stat(full_path)
        except IOError:  # Raised when the directory doesn't exist
            sftp_client.mkdir(full_path)


def do_file_copy(credential_id, remote_host_id, datafile_map, base_dir=None):
    if base_dir is None:
        base_dir = ['mytardis-data']
    elif isinstance(base_dir, str):
        base_dir = split_path(base_dir) + ['mytardis-data']

    credential = Credential.objects.get(pk=credential_id)
    ssh = credential.get_client_for_host(
        RemoteHost.objects.get(
            pk=remote_host_id))
    sftp_client = ssh.open_sftp()

    def unique_base_path(base, increment=0):
        base_copy = list(base)
        try:
            if increment > 0:
                suffix = "_%i" % increment
            else:
                suffix = ""
            base_copy[-1] += suffix
            sftp_client.stat('/'.join(base_copy))
            return unique_base_path(base, increment+1)
        except IOError:
            return base_copy

    base_dir = unique_base_path(base_dir)

    make_dirs(sftp_client, base_dir)

    for (_path, datafile) in datafile_map:
        path = list(_path)
        if datafile.directory is not None:
            path += datafile.directory.split('/')
        path = base_dir + path
        path_str = '/'.join(path + [datafile.filename])
        make_dirs(sftp_client, path)
        sftp_client.putfo(datafile.file_object, path_str, datafile.size)
