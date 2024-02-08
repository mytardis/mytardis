import uuid
from io import BytesIO

from paramiko import SFTPError


def shell_escape(s):
    return "'" + s.replace("'", "'\\''") + "'"


def is_directory(sftp, path):
    sftp.chdir(".")
    cwd = sftp.getcwd()
    try:
        sftp.chdir(path)
        return True
    except (SFTPError, IOError):
        return False
    finally:
        sftp.chdir(cwd)


def list_subdirectories(sftp_client, path, show_hidden=False):
    dir_list = [
        dir for dir in sftp_client.listdir(path) if is_directory(sftp_client, dir)
    ]
    if not show_hidden:
        return [dir for dir in dir_list if not dir.startswith(".")]
    return dir_list


def get_default_push_location(sftp_client):
    sftp_client.chdir(".")
    return sftp_client.getcwd()


def can_copy(sftp, object_type, object_id, path):
    if not is_directory(sftp, path):
        return False, "Directory does not exist."

    try:
        filename = "{}/.probe".format(path)
        sftp.putfo(BytesIO(str(uuid.uuid4()).encode()), filename)
        sftp.remove(filename)
    except:
        return False, "Destination is not writable."

    return True, ""
