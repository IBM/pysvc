from unittest import TestCase
from mock import patch, MagicMock
from pysvc.unified.scp_cli_client import ScpClient
from pysvc.unified.errors import *
from socket import timeout as _SocketTimeout


class TestScpCliClient(TestCase):

    def setUp(self):
        self.transport = MagicMock()
        self.scp_client = ScpClient(self.transport)

    def tearDown(self):
        pass

    def test_ssh_open_channel(self):
        self.scp_client._ssh_open_channel()
        self.transport.open_session.assert_called_with()

    def test_initial_timeout(self):
        timeout = 1
        scp_client = ScpClient(self.transport, timeout)
        scp_client._ssh_open_channel()
        self.transport.open_session.return_value.settimeout.\
            assert_called_with(timeout)

    def test_scp_recv(self):
        channel = MagicMock()
        self.scp_client._scp_recv(channel, 5)
        channel.recv.assert_called_with(5)

    def test_scp_recv_raise_timeout(self):
        channel = MagicMock()
        channel.recv = MagicMock(side_effect=[_SocketTimeout()])
        with self.assertRaisesRegex(SCPTimeoutError,
                                     r'Timeout waiting for scp response'):
            self.scp_client._scp_recv(channel, 5)

    def test_extract_file_size_info(self):
        msg = r'C 5 /dumps/iostats'
        self.assertEqual(self.scp_client._extract_file_size_info(msg), 5)

    def test_scp_receive_file(self):
        msg = r'C 10 /dumps/iostats'
        channel = MagicMock()
        self.scp_client._scp_recv = MagicMock(side_effect=[
            'test '
            'strin',
            ['\x00']])
        self.scp_client._scp_receive_file(channel, msg)
        channel.sendall.assert_called_with('\x00')
        self.scp_client._scp_recv.assert_any_call(channel,
                                                  10)
        self.scp_client._scp_recv.assert_any_call(channel,
                                                  self.scp_client.msg_buf_size)

    def test_scp_receive_file_raise_SCPError(self):
        msg = r'C 10 /dumps/iostats'
        channel = MagicMock()
        self.scp_client._scp_recv = MagicMock(side_effect=[
            'test '
            'strin',
            []
        ])
        with self.assertRaisesRegex(SCPError,
                                     r'Error on end of read: msg is empty'):
            self.scp_client._scp_receive_file(channel, msg)

        self.scp_client._scp_recv = MagicMock(side_effect=[
            'test '
            'strin',
            ['random char']])

        with self.assertRaisesRegex(SCPError, r'Error on end of read'):
            self.scp_client._scp_receive_file(channel, msg)

    def test_scp_receive_file_raise_SocketTimeout(self):
        msg = r'C 10 /dumps/iostats'
        channel = MagicMock()
        self.scp_client._scp_recv = MagicMock(side_effect=[
            _SocketTimeout()])
        with self.assertRaisesRegex(SCPTimeoutError, r'Timeout on file read'):
            self.scp_client._scp_receive_file(channel, msg)

    def test_receive(self):
        remote_path = '/dumps/iostats/test'
        channel = MagicMock()
        channel.closed = False
        self.scp_client._ssh_open_channel = MagicMock(side_effect=[channel])
        self.scp_client._scp_recv = MagicMock(
            side_effect=[['C', r'C 10 /dumps/iostats']]
        )

        xml_context = r'<xml></xml>'
        self.scp_client._scp_receive_file = MagicMock(
            side_effect=[xml_context])

        res = self.scp_client.receive(remote_path)

        self.assertEqual(res, xml_context)

        channel.exec_command.assert_called_with(
            r'scp -f {}'.format(remote_path)
        )
        channel.sendall.assert_called_with('\x00')
        self.scp_client._scp_recv.assert_called_with(
            channel, self.scp_client.msg_buf_size
        )
        self.scp_client._scp_receive_file.assert_called_with(
            channel, [r'C 10 /dumps/iostats']
        )

    def test_receive_channel_close(self):
        remote_path = '/dumps/iostats/test'
        channel = MagicMock()
        channel.closed = True
        self.scp_client._ssh_open_channel = MagicMock(side_effect=[channel])
        self.scp_client._scp_recv = MagicMock(
            side_effect=[['C', r'C 10 /dumps/iostats']]
        )
        self.scp_client._scp_receive_file = MagicMock()

        res = self.scp_client.receive(remote_path)

        self.assertEqual(res, None)

    def test_receive_no_msg(self):
        remote_path = '/dumps/iostats/test'
        channel = MagicMock()
        channel.closed = False
        self.scp_client._ssh_open_channel = MagicMock(side_effect=[channel])
        self.scp_client._scp_recv = MagicMock(
            side_effect=[None]
        )
        self.scp_client._scp_receive_file = MagicMock()
        res = self.scp_client.receive(remote_path)

        self.assertEqual(res, None)

    def test_receive_raise_SCPError_scp_error(self):
        remote_path = '/dumps/iostats/test'
        channel = MagicMock()
        channel.closed = False
        self.scp_client._ssh_open_channel = MagicMock(side_effect=[channel])
        self.scp_client._scp_recv = MagicMock(
            side_effect=[['\x01', r'C 10 /dumps/iostats']]
        )

        xml_context = r'<xml></xml>'
        self.scp_client._scp_receive_file = MagicMock(
            side_effect=[xml_context])

        with self.assertRaisesRegex(SCPError, r'scp error'):
            self.scp_client.receive(remote_path)

    def test_receive_raise_SCPError_unknown(self):
        remote_path = '/dumps/iostats/test'
        channel = MagicMock()
        channel.closed = False
        self.scp_client._ssh_open_channel = MagicMock(side_effect=[channel])
        self.scp_client._scp_recv = MagicMock(
            side_effect=[['Random Char', r'C 10 /dumps/iostats']]
        )

        xml_context = r'<xml></xml>'
        self.scp_client._scp_receive_file = MagicMock(
            side_effect=[xml_context])

        with self.assertRaisesRegex(SCPError, r'Unknown scp reply'):
            self.scp_client.receive(remote_path)
