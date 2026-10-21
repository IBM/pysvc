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
'''Test for SSH transport send_command timeouts'''

import socket
import unittest
from unittest import mock

from paramiko.ssh_exception import SSHException

from pysvc.errors import UnableToConnectException
from pysvc.transports.ssh_transport import SSHTransport


class TestSendCommandOpenSession(unittest.TestCase):

    def setUp(self):
        self.transport = SSHTransport('1.2.3.4', 'user', 'password',
                                      cmd_timeout=30.0)
        self.paramiko_transport = mock.MagicMock()
        self.transport.transport = mock.MagicMock()
        self.transport.transport.get_transport.return_value = \
            self.paramiko_transport
        self.channel = self.paramiko_transport.open_session.return_value

    def test_open_session_and_channel_use_default_cmd_timeout(self):
        self.transport.send_command('lsvdisk')

        self.paramiko_transport.open_session.assert_called_once_with(
            timeout=30.0)
        self.channel.settimeout.assert_called_once_with(30.0)

    def test_open_session_and_channel_use_given_timeout(self):
        self.transport.send_command('lsvdisk', timeout=5)

        self.paramiko_transport.open_session.assert_called_once_with(
            timeout=5)
        self.channel.settimeout.assert_called_once_with(5)

    def _assert_open_session_failure_closes_transport(self, error):
        self.paramiko_transport.open_session.side_effect = error

        with self.assertRaises(UnableToConnectException):
            self.transport.send_command('lsvdisk')

        self.paramiko_transport.close.assert_called_once_with()
        self.channel.exec_command.assert_not_called()

    def test_open_session_timeout_closes_transport_and_raises(self):
        self._assert_open_session_failure_closes_transport(
            SSHException('Timeout opening channel.'))

    def test_open_session_eof_closes_transport_and_raises(self):
        self._assert_open_session_failure_closes_transport(EOFError())

    def test_close_failure_does_not_hide_original_error(self):
        self.paramiko_transport.open_session.side_effect = SSHException(
            'Timeout opening channel.')
        self.paramiko_transport.close.side_effect = OSError('close failed')

        with self.assertRaises(UnableToConnectException):
            self.transport.send_command('lsvdisk')

    def test_raised_error_can_be_converted_to_string(self):
        self.paramiko_transport.open_session.side_effect = SSHException(
            'Timeout opening channel.')

        with self.assertRaises(UnableToConnectException) as context:
            self.transport.send_command('lsvdisk')

        self.assertIn('Timeout opening channel.', str(context.exception))


class TestConfigureKeepalive(unittest.TestCase):

    LINUX_OPTIONS = (('TCP_KEEPIDLE', 15),
                     ('TCP_KEEPINTVL', 5),
                     ('TCP_KEEPCNT', 3),
                     ('TCP_USER_TIMEOUT', 30000))

    def setUp(self):
        self.transport = SSHTransport('1.2.3.4', 'user', 'password')
        self.paramiko_transport = mock.MagicMock()
        self.transport.transport = mock.MagicMock()
        self.transport.transport.get_transport.return_value = \
            self.paramiko_transport
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(self.sock.close)
        self.paramiko_transport.sock = self.sock

    def _get_option(self, level, name):
        return self.sock.getsockopt(level, name)

    def test_enables_ssh_level_keepalive(self):
        self.transport._configure_keepalive()

        self.paramiko_transport.set_keepalive.assert_called_once_with(15)

    def test_enables_tcp_keepalive_on_socket(self):
        self.transport._configure_keepalive()

        self.assertTrue(
            self._get_option(socket.SOL_SOCKET, socket.SO_KEEPALIVE))

    def test_sets_available_linux_options(self):
        self.transport._configure_keepalive()

        for name, value in self.LINUX_OPTIONS:
            if hasattr(socket, name):
                self.assertEqual(
                    value,
                    self._get_option(socket.IPPROTO_TCP,
                                     getattr(socket, name)),
                    name)

    def test_skips_options_missing_on_platform(self):
        sock = mock.MagicMock(spec=socket.socket)
        self.paramiko_transport.sock = sock

        with mock.patch.object(socket, 'TCP_KEEPIDLE', create=True,
                               new=100), \
                mock.patch.object(socket, 'TCP_KEEPINTVL', create=True,
                                  new=101), \
                mock.patch.object(socket, 'TCP_KEEPCNT', create=True,
                                  new=102):
            if hasattr(socket, 'TCP_USER_TIMEOUT'):
                self.addCleanup(setattr, socket, 'TCP_USER_TIMEOUT',
                                socket.TCP_USER_TIMEOUT)
                del socket.TCP_USER_TIMEOUT
            self.transport._configure_keepalive()

        sock.setsockopt.assert_has_calls([
            mock.call(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            mock.call(socket.IPPROTO_TCP, 100, 15),
            mock.call(socket.IPPROTO_TCP, 101, 5),
            mock.call(socket.IPPROTO_TCP, 102, 3)])
        self.assertEqual(4, sock.setsockopt.call_count)

    def test_no_paramiko_transport_does_nothing(self):
        self.transport.transport.get_transport.return_value = None

        self.transport._configure_keepalive()

    def test_non_socket_object_is_skipped(self):
        self.paramiko_transport.sock = mock.MagicMock()

        self.transport._configure_keepalive()

        self.paramiko_transport.set_keepalive.assert_called_once_with(15)
        self.paramiko_transport.sock.setsockopt.assert_not_called()

    def test_failure_does_not_raise(self):
        self.paramiko_transport.set_keepalive.side_effect = OSError('boom')

        self.transport._configure_keepalive()

    def test_connect_configures_keepalive(self):
        self.transport._configure_keepalive = mock.MagicMock()

        self.transport.connect()

        self.transport.transport.connect.assert_called_once()
        self.transport._configure_keepalive.assert_called_once_with()
