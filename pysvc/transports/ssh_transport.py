##############################################################################
# Copyright 2025 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

from paramiko.ssh_exception import SSHException
from pysvc.transports.transport import CommonTransport
from paramiko import PKey
from paramiko import SSHClient
from paramiko.ssh_exception import PasswordRequiredException
from paramiko.ssh_exception import PartialAuthentication
from paramiko.ssh_exception import BadHostKeyException
from paramiko.ssh_exception import BadAuthenticationType
from paramiko.ssh_exception import AuthenticationException
from pysvc.errors import ConnectionTimedoutException
from pysvc.errors import TransportMessages
from pysvc.errors import IncorrectCredentials
from pysvc.errors import BadAuthenticationTypeException
from pysvc.errors import BadHostFingerPrintException
from pysvc.errors import PartialAuthenticationException
from pysvc.errors import PassphraseRequiredException
from pysvc.errors import HostDoesNotExistException
from pysvc.errors import UnableToConnectException
from logging import getLogger
from contextlib import contextmanager
from pysvc import PYSVC_DEFAULT_LOGGER
import hashlib
import paramiko
import socket
import os
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)


xlog = getLogger(PYSVC_DEFAULT_LOGGER)


class FIPSSafeAutoAddPolicy(paramiko.MissingHostKeyPolicy):
    """
    AutoAddPolicy compatible with FIPS-enabled environments.
    Adds unknown host keys to the client's host keys repository without invoking
    legacy MD5 get_fingerprint(), which fails under FIPS OpenSSL enforcement.
    """

    def missing_host_key(self, client, hostname, key):
        client._host_keys.add(hostname, key.get_name(), key)
        if client._host_keys_filename is not None:
            client.save_host_keys(client._host_keys_filename)
        try:
            fp_sha256 = hashlib.sha256(key.asbytes()).hexdigest()
            xlog.debug("Added %s host key for %s (SHA256: %s)",
                       key.get_name(), hostname, fp_sha256)
        except Exception:
            pass


class SSHTransport(CommonTransport):
    DEFAULT_SSH_PORT = 22

    def __init__(
            self,
            host,
            user=None,
            password=None,
            pkey=None,
            pkey_file=None,
            port=22,
            timeout=30,
            auto_add=True,
            cmd_timeout=30.0,
            ignore_known_hosts=True,
            keepalive_interval=15,
            tcp_keepidle=15,
            tcp_keepintvl=5,
            tcp_keepcnt=3,
            tcp_user_timeout=30000):
        """
        Constructor for common SSH trasport class.
        pkey        : Key object used to sign and verify SSH2 data;
        pkey_file   : File name of the private keys to try for
                      SSH authentication;
        timeout     : Timeout value for establishing a ssh connection;
        auto_add    : If the specified mamagement node cannot be identified,
                      whether I should auto add it to known host list and
                      save to a local file;
        cmd_timeout : Timeout valeu for a command to return;
        keepalive_interval : Seconds between SSH keepalive messages;
        tcp_keepidle       : Seconds of idle time before TCP keepalive
                             probes start;
        tcp_keepintvl      : Seconds between TCP keepalive probes;
        tcp_keepcnt        : Unanswered TCP keepalive probes before the
                             connection is closed;
        tcp_user_timeout   : Milliseconds that sent data may stay
                             unacknowledged before the connection is closed.
        A keepalive value of None leaves that setting untouched. The TCP
        options are Linux-only and are skipped where they do not exist.
        """
        super(SSHTransport, self).__init__()
        self.host = host
        self.user = user
        self.password = password
        self.pkey = pkey
        self.private_key = pkey_file
        self.port = port
        self.timeout = timeout
        self.cmd_exec_timeout = cmd_timeout
        self.keepalive_interval = keepalive_interval
        self.tcp_keepidle = tcp_keepidle
        self.tcp_keepintvl = tcp_keepintvl
        self.tcp_keepcnt = tcp_keepcnt
        self.tcp_user_timeout = tcp_user_timeout
        self.connected_endpoint = None
        self.auto_add_unknown_hosts = auto_add
        self.transport = SSHClient()
        self.sftp_client = None
        self.is_client_connected = False
        self.is_known_hosts_ignored = ignore_known_hosts
        self.svc_client_host_keys_file = \
            "%s/xsf_known_hosts" % os.path.expanduser("~")
        if self.pkey is not None:
            if not isinstance(self.pkey, PKey):
                xlog.debug(TransportMessages.SSH_INCORRECT_PRIVATE_KEY)
                raise IncorrectCredentials(
                    message=TransportMessages.SSH_INCORRECT_PRIVATE_KEY)

        if (os.path.isfile(self.svc_client_host_keys_file) and
                self.is_known_hosts_ignored is False):
            try:
                self.transport.load_host_keys(
                    filename=self.svc_client_host_keys_file)
            except IOError as ex:
                xlog.debug(ex)
                raise IncorrectCredentials(
                    message=TransportMessages.SSH_FAILED_TO_LOAD_KNOWN_HOSTS,
                    original_exception=ex)

    def __str__(self):
        if self.port == self.DEFAULT_SSH_PORT:
            return self.host
        return 'ssh://%s:%s' % (self.host, self.port)

    def __repr__(self):
        return '<%s>' % self

    @contextmanager
    def _exception_handler(self):
        try:
            yield
        except BadAuthenticationType as ex:
            xlog.debug(ex)
            raise BadAuthenticationTypeException(
                allowed_types=ex.allowed_types, original_exception=ex)
        except BadHostKeyException as ex:
            xlog.debug(ex)
            raise BadHostFingerPrintException(
                hostname=ex.hostname,
                expected_key=ex.expected_key,
                presented_key=ex.key,
                original_exception=ex)
        except PartialAuthentication as ex:
            xlog.debug(ex)
            raise PartialAuthenticationException(
                allowed_types=ex.allowed_types, original_exception=ex)
        except PasswordRequiredException as ex:
            xlog.debug(ex)
            raise PassphraseRequiredException(
                message=TransportMessages.SSH_PASS_PHRASE_REQUIRED,
                original_exception=ex)
        except AuthenticationException as ex:
            xlog.debug(ex)
            raise IncorrectCredentials(
                message=TransportMessages.SSH_AUTHENTICATION_FAILURE,
                original_exception=ex)
        except socket.timeout as ex:
            xlog.debug(ex)
            raise ConnectionTimedoutException(
                message=TransportMessages.SSH_CONNECT_TIMED_OUT,
                original_exception=ex)
        except (socket.herror, socket.gaierror) as ex:
            xlog.debug(ex)
            raise HostDoesNotExistException(
                hostname=self.host, original_exception=ex)
        except (SSHException, socket.error) as ex:
            xlog.debug(ex)
            raise UnableToConnectException(
                message=TransportMessages.SSH_UNABLE_TO_CONNECT(
                    self.host), original_exception=ex)

    def connect(self):
        """
        Initialize a SSH connection with properties
        which were set up in constructor.
        """
        with self._exception_handler():
            if self.auto_add_unknown_hosts:
                self.transport.set_missing_host_key_policy(
                    FIPSSafeAutoAddPolicy())
            self.transport.connect(
                self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                pkey=self.pkey,
                key_filename=self.private_key,
                timeout=self.timeout)
            self.connected_endpoint = self.host
            self.is_client_connected = True
            self._configure_keepalive()
            if self.is_known_hosts_ignored is False:
                self.transport.save_host_keys(self.svc_client_host_keys_file)

    def is_connected(self):
        return self.is_client_connected

    def disconnect(self):
        """
        Disconnect from the SSH server.
        """
        if self.is_client_connected:
            self.transport.close()
            self.is_client_connected = False

    def reconnect(self):
        self.disconnect()
        self.connect()

    def _configure_keepalive(self):
        """Let the kernel detect a dead peer, also when idle (within ~30-45s
        with the default values).
        Failures here must never break the connection itself, and a failure
        to set one option must not skip the others."""
        try:
            ssh_transport = self.transport.get_transport()
        except Exception as ex:
            xlog.debug("Failed to get SSH transport for keepalive: %s", ex)
            return
        if ssh_transport is None:
            return
        if self.keepalive_interval is not None:
            try:
                # SSH-level keepalive, seconds
                ssh_transport.set_keepalive(self.keepalive_interval)
            except Exception as ex:
                xlog.debug("Failed to set SSH keepalive: %s", ex)
        sock = getattr(ssh_transport, "sock", None)
        if not isinstance(sock, socket.socket):
            return
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except Exception as ex:
            xlog.debug("Failed to set SO_KEEPALIVE: %s", ex)
        # Linux-only options, skipped where they do not exist (e.g. macOS)
        for name, value in (("TCP_KEEPIDLE", self.tcp_keepidle),
                            ("TCP_KEEPINTVL", self.tcp_keepintvl),
                            ("TCP_KEEPCNT", self.tcp_keepcnt),
                            ("TCP_USER_TIMEOUT", self.tcp_user_timeout)):
            if value is None or not hasattr(socket, name):
                continue
            try:
                sock.setsockopt(socket.IPPROTO_TCP, getattr(socket, name),
                                value)
            except Exception as ex:
                xlog.debug("Failed to set %s: %s", name, ex)

    def _close_ssh_transport(self):
        """Close the underlying paramiko transport so is_active() returns
        False. The SSHClient object is kept, so callers that use
        client.transport.transport.get_transport() still get an object."""
        try:
            ssh_transport = self.transport.get_transport()
            if ssh_transport is not None:
                ssh_transport.close()
        except Exception as ex:
            xlog.debug("Error while closing SSH transport: %s", ex)

    def send_command(
            self,
            command,
            buf_size=-1,
            raw=False,
            timeout=0,
            stdin_input=None):
        with self._exception_handler():
            # return self.transport.exec_command(command)
            cmd_timeout = timeout or self.cmd_exec_timeout
            channel = None
            try:
                try:
                    channel = self.transport.get_transport().open_session(
                        timeout=cmd_timeout)
                except (SSHException, EOFError) as ex:
                    # The channel could not be opened in time, or the
                    # transport died while waiting (e.g. peer stopped
                    # answering). Mark the transport dead so the pool
                    # replaces it instead of reusing it.
                    xlog.error("Failed to open SSH channel to %s: %r",
                               self.host, ex)
                    self._close_ssh_transport()
                    raise UnableToConnectException(
                        message=TransportMessages.SSH_UNABLE_TO_CONNECT(
                            self.host),
                        original_exception=[ex])
                channel.settimeout(cmd_timeout)
                channel.exec_command(command)
                stdin = channel.makefile('wb', buf_size)
                stdout = channel.makefile('rb', buf_size)
                stderr = channel.makefile_stderr('rb', buf_size)
                if stdin_input is not None:
                    stdin.write(stdin_input)
                    stdin.flush()
                    # shutdown_write to close write channel, paramiko will send
                    # EOF to device.
                    channel.shutdown_write()
                if raw:  # gain performance without spliting line
                    return stdin, stdout.read(), stderr.read()
                return stdin, stdout.readlines(), stderr.readlines()
            except socket.timeout as ex:
                # Need to reconnect to terminate the remote method call
                self.reconnect()
                xlog.error(ex)
                raise ConnectionTimedoutException(
                    message=TransportMessages.SSH_CON_TIMED_OUT_WHEN_EXEC_CMD,
                    original_exception=ex)
            finally:
                # Do not rely on garbage collection to release the channel.
                if channel is not None:
                    try:
                        channel.close()
                    except Exception as ex:
                        xlog.debug("Error while closing SSH channel: %s", ex)
