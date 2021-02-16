import random

from paramiko import SFTPError

from tardis.tardis_portal.models import Experiment, Dataset, DataFile


def shell_escape(s):
    return "'" + s.replace("'", "'\\''") + "'"


def bytes_available(ssh, path):
    try:
        _, stdout, _ = ssh.exec_command("df -k %s | tail -n 1" % shell_escape(path))
        cmd_output = stdout.read().split()
    except Exception as e:
        cmd_output = str(e)

    # df can output the size in a couple of ways; try to detect which
    # and return the bytes available
    if len(cmd_output) == 5:
        return int(cmd_output[2]) * 1024
    if len(cmd_output) == 6:
        return int(cmd_output[3]) * 1024

    return -1


def is_directory(sftp_client, path):
    sftp_client.chdir('.')
    cwd = sftp_client.getcwd()
    try:
        sftp_client.chdir(path)
        return True
    except (SFTPError, IOError):
        return False
    finally:
        sftp_client.chdir(cwd)


def list_subdirectories(sftp_client, path, show_hidden=False):
    dir_list = [dir for dir in sftp_client.listdir(path) if
                is_directory(sftp_client, dir)]
    if not show_hidden:
        return [dir for dir in dir_list if not dir.startswith('.')]
    return dir_list


def get_default_push_location(sftp_client):
    sftp_client.chdir('.')
    return sftp_client.getcwd()


def get_object_size(type, id):
    for obj_type in [Experiment, Dataset, DataFile]:
        if obj_type.__name__.lower() == type.lower():
            return obj_type.objects.get(pk=id).get_size()
    raise TypeError("Object of type %s does not exist" % type)


def can_copy(ssh_client, object_type, object_id, path):
    if not is_directory(ssh_client.open_sftp(), path):
        return False, "Directory does not exist."

    # check if destination is writable by touching a file and deleting it
    chan = ssh_client.get_transport().open_session()
    test_file_name = "%032x" % random.getrandbits(128)
    chan.exec_command(
        "touch {destination}/{test_file_name} && "
        "rm {destination}/{test_file_name}".format(
            destination=path, test_file_name=test_file_name))
    status = chan.recv_exit_status()
    chan.close()
    if status != 0:
        return False, "Destination is not writable"

    try:
        if bytes_available(ssh_client, path) > get_object_size(object_type, object_id):
            return True, ''
        return False, 'Insufficient disk space'
    except (Experiment.DoesNotExist, Dataset.DoesNotExist, TypeError):
        return False, ''
