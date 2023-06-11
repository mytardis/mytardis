"""
SFTP Server
"""
# pylint: disable=C0411,C0412,C0413
# disabling import order check for monkey patching

import socketserver
import base64
import collections
import logging
import os
import stat
import time
import uuid

from paramiko.py3compat import StringIO

from django.conf import settings
from paramiko import (
    InteractiveQuery,
    RSAKey,
    ServerInterface,
    SFTPAttributes,
    SFTPHandle,
    SFTPServer,
    SFTPServerInterface,
    Transport,
    SSHException,
)
from paramiko import (
    OPEN_SUCCEEDED,
    OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED,
    SFTP_OP_UNSUPPORTED,
    SFTP_NO_SUCH_FILE,
)
from paramiko.common import AUTH_FAILED, AUTH_SUCCESSFUL
from paramiko.rsakey import RSAKey

from tardis.analytics import tracker
from tardis.tardis_portal.download import make_mapper
from tardis.tardis_portal.models import DataFile, Experiment, User
from tardis.tardis_portal.util import split_path

from .models import SFTPPublicKey

logger = logging.getLogger(__name__)
path_mapper = make_mapper(settings.DEFAULT_PATH_MAPPER, rootdir=None)

paramiko_log = logging.getLogger("paramiko.transport")
paramiko_log.disabled = True


# django db related modules must be imported after monkey-patching
from django.contrib.sites.models import Site  # noqa
from django.contrib.auth.models import AnonymousUser  # noqa


class DynamicTree(object):
    def __init__(self, host_obj=None):
        self.name = None
        self.obj = None  # an object if applicable
        self.update = self.update_nothing
        self.last_updated = None  # a time.time() number
        self.host_obj = host_obj
        self.children = None
        self.clear_children()

    def update_nothing(self):
        pass

    def clear_children(self):
        self.children = collections.defaultdict(lambda: DynamicTree(self.host_obj))

    def add_path(self, path):
        path = path.strip("/")
        elems = split_path(path)
        return self.add_path_elems(elems)

    def add_path_elems(self, elems):
        first = elems[0]
        leaf = self.children[first]
        leaf.name = first
        if len(elems) > 1:
            return leaf.add_path_elems(elems[1:])
        return leaf

    def add_child(self, name, obj=None):
        new_child = self.children[name]
        new_child.name = name
        new_child.obj = obj

    def get_leaf(self, path, update=False):
        path = path.strip("/")
        elems = collections.deque(split_path(path))
        leaf = self.children.get(elems.popleft())
        if leaf and update:
            leaf.update()
        while elems:
            leaf = leaf.children.get(elems.popleft())
            if leaf and update:
                leaf.update()
        return leaf

    def update_experiments(self):
        exps = [(path_mapper(exp), exp) for exp in self.host_obj.experiments]
        self.clear_children()
        for exp_name, exp in exps:
            child = self.children[exp_name]
            child.name = exp_name
            child.obj = exp
            child.update = child.update_datasets

    def update_datasets(self):
        all_files_name = "00_all_files"
        datasets = [(path_mapper(ds), ds) for ds in self.obj.datasets.all()]
        self.clear_children()
        for ds_name, ds in datasets:
            if ds_name == all_files_name:
                ds_name = "%s_dataset" % all_files_name
            child = self.children[ds_name]
            child.name = ds_name
            child.obj = ds
            child.update = child.update_dataset_files
        child = self.children[all_files_name]
        child.name = all_files_name
        child.obj = self.obj
        child.update = child.update_all_files

    def update_all_files(self):
        self.clear_children()
        for df in DataFile.objects.filter(dataset__experiments=self.obj).iterator():
            self._add_file_entry(df)

    def update_dataset_files(self):
        self.clear_children()
        for df in self.obj.datafile_set.all().iterator():
            self._add_file_entry(df)

    def _add_file_entry(self, datafile):
        df_name = path_mapper(datafile)
        # try:
        #     file_obj = df.file_object
        #     file_name = df_name
        # except IOError:
        #     file_name = df_name + "_offline"
        #     if getattr(settings, 'DEBUG', False):
        #         placeholder = df.file_objects.all()[0].uri
        #     else:
        #         placeholder = 'offline file, contact administrator'
        #     file_obj = StringIO(placeholder)
        # child = self.children[file_name]
        # child.name = file_name
        # child.obj = file_obj

        def add_unique_name(children, orig_name):
            counter = 1
            name = orig_name
            while name in children:
                counter += 1
                name = "%s_%i" % (orig_name, counter)
            return name, children[name]

        if datafile.directory:
            path = self.add_path(datafile.directory)
            df_name, child = add_unique_name(path.children, df_name)
        else:
            df_name, child = add_unique_name(self.children, df_name)
        child.name = df_name
        child.obj = datafile


class MyTSFTPServerInterface(SFTPServerInterface):
    """
    MyTardis data via SFTP
    """

    _cache_time = 60  # in seconds
    _exps_cache = {}

    def __init__(self, server, *args, **kwargs):
        """
        :param ServerInterface server: the server object associated with this
            channel and SFTP subsystem
        :param list args:
        :param dict kwargs:
        """
        self.server = server
        self.client_ip = kwargs.get("client_ip", "")

    @property
    def experiments(self):
        u = self.user.username
        if u not in self._exps_cache:
            self._exps_cache[u] = {"all": None, "last_update": None}
        if self._exps_cache[u]["all"] is None:
            self._exps_cache[u]["all"] = Experiment.safe.all(user=self.user)
            self._exps_cache[u]["last_update"] = time.time()
        elif self._exps_cache[u]["last_update"] - time.time() > self._cache_time:
            self._exps_cache[u]["all"]._result_cache = None
        return self._exps_cache[u]["all"]

    def session_started(self):
        """
        run on connection initialisation
        """
        self.user = self.server.user
        self.uuid = str(uuid.uuid4())
        tracker.track_login(
            "sftp", session_id=self.uuid, ip=self.client_ip, user=self.user
        )
        self.username = self.server.user.username
        self.cwd = "/home/%s" % self.username
        self.tree = DynamicTree(self)
        self.tree.name = "/"
        self.tree.add_path(self.cwd)
        exp_leaf = self.tree.add_path(os.path.join(self.cwd, "experiments"))
        exp_leaf.update = exp_leaf.update_experiments

    def session_ended(self):
        """
        run cleanup on exceptions or disconnection.
        idea: collect stats and store them in this function
        """
        tracker.track_logout(
            "sftp", session_id=self.uuid, ip=self.client_ip, user=self.user
        )

    def open(self, path, flags, attr):
        """
        Open a file on the server and create a handle for future operations
        on that file.  On success, a new object subclassed from L{SFTPHandle}
        should be returned.  This handle will be used for future operations
        on the file (read, write, etc).  On failure, an error code such as
        L{SFTP_PERMISSION_DENIED} should be returned.

        C{flags} contains the requested mode for opening (read-only,
        write-append, etc) as a bitset of flags from the C{os} module:

            - C{os.O_RDONLY}
            - C{os.O_WRONLY}
            - C{os.O_RDWR}
            - C{os.O_APPEND}
            - C{os.O_CREAT}
            - C{os.O_TRUNC}
            - C{os.O_EXCL}

        (One of C{os.O_RDONLY}, C{os.O_WRONLY}, or C{os.O_RDWR} will always
        be set.)

        The C{attr} object contains requested attributes of the file if it
        has to be created.  Some or all attribute fields may be missing if
        the client didn't specify them.

        @note: The SFTP protocol defines all files to be in "binary" mode. \
            There is no equivalent to python's "text" mode.

        :param basestring path: the requested datafile path
        :param int flags: flags or'd together from the C{os} module indicating \
            the requested mode for opening the file.
        :param SFTPAttributes attr: requested attributes of the file if it is \
            newly created.
        :returns: a new L{SFTPHandle} I{or error code}.
        :rtype: SFTPHandle
        """
        leaf = self.tree.get_leaf(path)
        tracker.track_download(
            "sftp",
            session_id=self.uuid,
            ip=self.client_ip,
            user=self.user,
            total_size=leaf.obj.size,
            num_files=1,
        )
        return MyTSFTPHandle(leaf.obj, flags, attr)

    def list_folder(self, path):
        """
        Returns a list of files within a given folder.  The C{path} will use
        posix notation (C{"/"} separates folder names) and may be an absolute
        or relative path.

        The list of files is expected to be a list of L{SFTPAttributes}
        objects, which are similar in structure to the objects returned by
        C{os.stat}.  In addition, each object should have its C{filename}
        field filled in, since this is important to a directory listing and
        not normally present in C{os.stat} results.

        In case of an error, you should return one of the C{SFTP_*} error
        codes, such as L{SFTP_PERMISSION_DENIED}.

        @param path: the requested path (relative or absolute) to be listed.
        @type path: str
        @return: a list of the files in the given folder, using \
            L{SFTPAttributes} objects.
        @rtype: list of L{SFTPAttributes} I{or error code}
        """
        path = os.path.normpath(path)
        leaf = self.tree.get_leaf(path, update=True)
        stats = [self.stat(os.path.join(path, child)) for child in leaf.children.keys()]
        return stats

    def stat(self, path):
        """
        Return an L{SFTPAttributes} object for a path on the server, or an
        error code.  If your server supports symbolic links (also known as
        "aliases"), you should follow them.  (L{lstat} is the corresponding
        call that doesn't follow symlinks/aliases.)

        @param path: the requested path (relative or absolute) to fetch \
            file statistics for.
        @type path: str

        @return: an attributes object for the given file, or an SFTP error \
            code (like L{SFTP_PERMISSION_DENIED}).
        @rtype: L{SFTPAttributes} I{or error code}
        """
        leaf = self.tree.get_leaf(path, update=False)
        if leaf is None:
            leaf = self.tree.get_leaf(path, update=True)
            if leaf is None:
                return SFTP_NO_SUCH_FILE
        sftp_stat = SFTPAttributes()
        sftp_stat.filename = leaf.name
        sftp_stat.st_size = int(getattr(leaf.obj, "size", 1))
        if not isinstance(leaf.obj, DataFile):
            sftp_stat.st_mode = 0o777 | stat.S_IFDIR
        else:
            sftp_stat.st_mode = 0o777 | stat.S_IFREG
        sftp_stat.st_uid = self.user.id
        sftp_stat.st_gid = 20
        sftp_stat.st_atime = time.time()
        sftp_stat.st_mtime = time.time()
        return sftp_stat

    def lstat(self, path):
        """
        symbolic links are not supported
        """
        return self.stat(path)

    def canonicalize(self, path):
        """
        Return the canonical form of a path on the server.
        """
        if path == ".":
            return self.cwd
        return os.path.normpath(path)


class MyTSFTPHandle(SFTPHandle):
    """
    SFTP File Handle
    """

    def __init__(self, df, flags=0, optional_args=None):
        """
        Create a new file handle

        :param DataFile df: DataFile
        :param int flags: optional flags as passed \
            to L{SFTPServerInterface.open}
        :param None optional_args: unused
        """
        super().__init__(flags=flags)
        try:
            self.readfile = df.file_object
        except IOError:
            if getattr(settings, "DEBUG", False):
                fo = df.file_objects.all()[0]
                error_string = "%s:%s" % (fo.storage_box.name, fo.uri)
                self.readfile = StringIO(error_string)

    def stat(self):
        """
        Return an L{SFTPAttributes} object referring to this open file, or an
        error code.  This is equivalent to L{SFTPServerInterface.stat}, except
        it's called on an open file instead of a path.

        @return: an attributes object for the given file, or an SFTP error \
            code (like L{SFTP_PERMISSION_DENIED}).
        @rtype: L{SFTPAttributes} I{or error code}
        """
        return SFTP_OP_UNSUPPORTED


class MyTServerInterface(ServerInterface):
    def __init__(self):
        super().__init__()
        self.username = None
        self.user = None

    def get_allowed_auths(self, username):
        auth_methods = ["password", "keyboard-interactive", "publickey"]
        # if user_has_key_set_up:
        #     auth_methods.append('publickey')
        return ",".join(auth_methods)

    def myt_auth(self, username, password):
        from tardis.tardis_portal.auth import auth_service

        class FakeRequest(object):
            POST = {}
            session = {}
            user = AnonymousUser()

        fake_request = FakeRequest()
        fake_request.POST = {"username": username, "password": password}
        user = auth_service.authenticate(
            request=fake_request, authMethod=None
        )  # checks all available methods
        if user and user.is_authenticated:
            # the following line is Australian Synchrotron specific and will
            # disappear when we start using their newer auth system
            user.epn_list = fake_request.session.get("_epn_list", [])
            self.username = username
            self.user = user
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def check_auth_password(self, username, password):
        return self.myt_auth(username, password)

    def check_auth_publickey(self, username, key):
        # get_django_pubkey
        # do_key_magic
        # return result
        user_keys = SFTPPublicKey.objects.filter(user__username=username)

        for uk in user_keys:
            user_key = RSAKey(data=base64.b64decode(uk.public_key))
            if key == user_key:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    logger.error("User with username %s does not exist.", username)
                if user.is_active:
                    self.username = username
                    self.user = user
                    return AUTH_SUCCESSFUL

        return AUTH_FAILED

    def check_auth_interactive(self, username, submethods):
        self.username = username
        query = InteractiveQuery()
        query.add_prompt("password: ", echo=False)
        return query

    def check_auth_interactive_response(self, responses):
        return self.myt_auth(self.username, responses[0])

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return OPEN_SUCCEEDED
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


class MyTSFTPServer(SFTPServer):
    """
    override SFTPServer to provide channel information to the SFTP subsystem
    """

    def __init__(self, *args, **kwargs):
        kwargs["client_ip"] = args[0].transport.getpeername()[0]
        super().__init__(*args, **kwargs)


class MyTSFTPRequestHandler(socketserver.BaseRequestHandler):
    timeout = 60
    auth_timeout = 60

    def setup(self):
        self.transport = Transport(self.request)
        self.transport.load_server_moduli()
        so = self.transport.get_security_options()
        so.digests = ("hmac-sha1",)
        so.compression = ("zlib@openssh.com", "none")
        self.transport.add_server_key(self.server.host_key)
        self.transport.set_subsystem_handler(
            "sftp", MyTSFTPServer, MyTSFTPServerInterface
        )

    def handle(self):
        try:
            self.transport.start_server(server=MyTServerInterface())
        except SSHException as e:
            logger.error("SSH error: %s" % str(e))
            self.transport.close()
        except EOFError as e:
            # Don't throw an error
            logger.warning("Socket error: %s" % str(e))
        except Exception as e:
            logger.error("Error: %s" % str(e))

    def handle_timeout(self):
        self.transport.close()


class MyTSFTPTCPServer(socketserver.TCPServer):
    # If the server stops/starts quickly, don't fail because of
    # "port in use" error.
    allow_reuse_address = True

    def __init__(self, address, host_key, RequestHandlerClass=None):
        self.host_key = host_key
        if RequestHandlerClass is None:
            RequestHandlerClass = MyTSFTPRequestHandler
        socketserver.TCPServer.__init__(self, address, RequestHandlerClass)

    def shutdown_request(self, request):
        # Prevent TCPServer from closing the connection prematurely
        return

    def close_request(self, request):
        # Prevent TCPServer from closing the connection prematurely
        return


def start_server(host=None, port=None, keyfile=None):
    """
    The SFTP_HOST_KEY setting is required for configuring SFTP access.
    The SFTP_PORT setting defaults to 2200.

    See: tardis/default_settings/sftp.py
    """
    if host is None:
        current_site = Site.objects.get_current()
        host = current_site.domain
    port = port or getattr(settings, "SFTP_PORT", 2200)
    try:
        host_key = RSAKey.from_private_key(keyfile or StringIO(settings.SFTP_HOST_KEY))
    except:
        raise SSHException("failed loading SFTP host key")
    server = MyTSFTPTCPServer((host, port), host_key=host_key)
    try:
        server.serve_forever()
    except (SystemExit, KeyboardInterrupt):
        server.server_close()
