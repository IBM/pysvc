##############################################################################
# Copyright 2019 IBM Corp.
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
import paramiko
import socket
import os
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)


xlog = getLogger(PYSVC_DEFAULT_LOGGER)


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
            ignore_known_hosts=True):
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
                    paramiko.AutoAddPolicy())
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

    def send_command(
            self,
            command,
            buf_size=-1,
            raw=False,
            timeout=0,
            stdin_input=None):
        with self._exception_handler():
            # return self.transport.exec_command(command)
            try:
                channel = self.transport.get_transport().open_session()
                channel.settimeout(timeout or self.cmd_exec_timeout)
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
