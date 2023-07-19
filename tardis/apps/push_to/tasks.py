import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

import pytz

from tardis.celery import tardis_app
from tardis.tardis_portal.models import DataFile, Dataset, Experiment
from tardis.tardis_portal.util import (
    get_filesystem_safe_dataset_name,
    get_filesystem_safe_experiment_name,
)

from .models import Credential, Progress, RemoteHost, Request


@tardis_app.task
def requests_maintenance(**kwargs):
    """
    Maintenance actions to cleanup data
    """
    requests = Request.objects.all()
    for req in requests:
        total_files = Progress.objects.filter(request=req).count()
        completed_files = Progress.objects.filter(request=req, status=1).count()
        if completed_files == total_files:
            # Successfully completed request
            req.delete()
        else:
            tz = pytz.timezone(settings.TIME_ZONE)
            wait_until = datetime.now(tz) - timedelta(hours=24*7)
            if req.timestamp < wait_until:
                # Delete any requests after one week
                # This time should be sufficient to do any debugging
                req.delete()
            elif req.message is None:
                files = Progress.objects.filter(request=req, status=0, retry__lt=10).count()
                if files != 0:
                    # Try process again if there are files with re-try attempts left
                    process_request.apply_async(args=[req.id], countdown=60)


@tardis_app.task
def push_experiment_to_host(user_id, credential_id, remote_host_id,
                            experiment_id, base_dir=None):
    req = Request.objects.create(
        user=User.objects.get(pk=user_id),
        object_type="experiment",
        object_id=experiment_id,
        credential=Credential.objects.get(pk=credential_id),
        host=RemoteHost.objects.get(pk=remote_host_id),
        base_dir=base_dir)

    datasets = Dataset.objects.filter(experiments=Experiment.objects.get(pk=experiment_id))
    for ds in datasets:
        datafiles = DataFile.objects.filter(dataset=ds)
        for df in datafiles:
            Progress.objects.create(request=req, datafile=df)

    process_request.apply_async(args=[req.id])

@tardis_app.task
def push_dataset_to_host(user_id, credential_id, remote_host_id,
                         dataset_id, base_dir=None):
    req = Request.objects.create(
        user=User.objects.get(pk=user_id),
        object_type="dataset",
        object_id=dataset_id,
        credential=Credential.objects.get(pk=credential_id),
        host=RemoteHost.objects.get(pk=remote_host_id),
        base_dir=base_dir)

    datafiles = DataFile.objects.filter(dataset=Dataset.objects.get(pk=dataset_id))
    for df in datafiles:
        Progress.objects.create(request=req, datafile=df)

    process_request.apply_async(args=[req.id])


@tardis_app.task
def push_datafile_to_host(user_id, credential_id, remote_host_id,
                          datafile_id, base_dir=None):
    req = Request.objects.create(
        user=User.objects.get(pk=user_id),
        object_type="datafile",
        object_id=datafile_id,
        credential=Credential.objects.get(pk=credential_id),
        host=RemoteHost.objects.get(pk=remote_host_id),
        base_dir=base_dir)

    Progress.objects.create(request=req, datafile=DataFile.objects.get(pk=datafile_id))

    process_request.apply_async(args=[req.id])


@tardis_app.task(ignore_result=True)
def process_request(request_id, idle=0):
    req = Request.objects.get(pk=request_id)
    files = Progress.objects.filter(request=req, status=0, retry__lt=10)
    no_errors = True

    try:
        ssh = req.credential.get_client_for_host(req.host)
        # https://github.com/paramiko/paramiko/issues/175#issuecomment-24125451
        transport = ssh.get_transport()
        transport.default_window_size = 2147483647
        transport.packetizer.REKEY_BYTES = pow(2, 40)
        transport.packetizer.REKEY_PACKETS = pow(2, 40)
        sftp = ssh.open_sftp()
    except Exception as err:
        # Authentication failed (expired?)
        req.message = "Can't connect: %s" % str(err)
        req.save()
        return

    remote_base_dir = []
    if req.base_dir is not None:
        remote_base_dir.append(req.base_dir)

    remote_base_dir.append("mytardis-{}".format(req.id))

    if req.object_type == "experiment":
        experiment = Experiment.objects.get(pk=req.object_id)
        remote_base_dir.append(get_filesystem_safe_experiment_name(experiment))

    make_dirs(sftp, remote_base_dir)

    for file in files:
        file.timestamp = timezone.now()
        src_file = file.datafile.get_absolute_filepath()
        if src_file is not None and os.path.exists(src_file):
            try:
                path = [get_filesystem_safe_dataset_name(file.datafile.dataset)]
                if file.datafile.directory is not None:
                    path += file.datafile.directory.split('/')
                path = remote_base_dir + path
                make_dirs(sftp, path)
                path_str = "/".join(path + [file.datafile.filename])
                sftp.putfo(file.datafile.get_file(), path_str, file.datafile.size)
                file.status = 1
            except Exception as e:
                no_errors = False
                file.retry += 1
                file.message = str(e)
        else:
            no_errors = False
            file.retry += 1
            file.message = "Can't find source file."
        file.save()
        if not no_errors and file.message is not None and (
                "Socket is closed" in file.message or
                "Server connection dropped" in file.message):
            break

    sftp.close()
    ssh.close()

    if no_errors:
        complete_request(req.id)
    else:
        process_request.apply_async(args=[req.id, idle+1], countdown=(idle+1)*60)


def complete_request(request_id):
    req = Request.objects.get(pk=request_id)
    total_files = Progress.objects.filter(request=req).count()
    completed_files = Progress.objects.filter(request=req, status=1).count()

    send_email = False

    if completed_files == total_files:
        send_email = True
        subject = "Data pushed successfully"
        message = "Your recent push-to request was completed successfully!\n" \
                  "Log in to %s to access the requested data in %s folder." % (
                    req.host.nickname,
                    "mytardis-{}".format(req.id))
    else:
        files = Progress.objects.filter(request=req, status=0, retry__lt=10).count()
        if files != 0:
            process_request.apply_async(args=[req.id], countdown=600)
        else:
            send_email = True
            subject = "Data push failed"
            message = "Your recent push-to request %s to %s encountered an error and " \
                      "could not be completed.\n" \
                      "We have completed transfer for %s out of %s files.\n" \
                      "Contact support for more information." % (
                        req.id,
                        req.host.nickname,
                        completed_files, total_files)

    if send_email:
        req.user.email_user(subject, message,
                            from_email=getattr(settings, "PUSH_TO_FROM_EMAIL", None),
                            fail_silently=True)


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
