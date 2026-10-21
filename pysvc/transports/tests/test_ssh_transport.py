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
