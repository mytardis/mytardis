from paramiko import SFTPError


def shell_escape(s):
    return "'" + s.replace("'", "'\\''") + "'"


def bytes_available(ssh_client, path):
    stdin, stdout, stderr = ssh_client.exec_command(
        'df %s | tail -n 1' % shell_escape(path))
    cmd_output = stdout.read().split()

    # df can output the size in a couple of ways; try to detect which
    # and return the bytes available
    try:
        if len(cmd_output) == 5:
            return int(cmd_output[2])
        elif len(cmd_output) == 6:
            return int(cmd_output[3])
    except ValueError:
        pass
    return "unknown"


def is_directory(sftp_client, path):
    sftp_client.chdir('.')
    cwd = sftp_client.getcwd()
    try:
        sftp_client.chdir(path)
        return True
    except SFTPError:
        return False
    finally:
        sftp_client.chdir(cwd)


def list_subdirectories(sftp_client, path, show_hidden=False):
    dir_list = [dir for dir in sftp_client.listdir(path) if is_directory(sftp_client, dir)]
    if not show_hidden:
        return [dir for dir in dir_list if not dir.startswith('.')]
    else:
        return dir_list